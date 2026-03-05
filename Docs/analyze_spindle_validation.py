#!/usr/bin/env python3
"""
Spindle validation analyzer for grblHAL PWM linearization.

Input CSV columns:
  S,VFD_Hz,Tach_RPM,Note

Example:
  python3 analyze_spindle_validation.py spindle_validation_template.csv --rpm-max 11867.5 --pwm-min 4.167
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from statistics import median
from typing import List, Optional


@dataclass
class Row:
    s: float
    vfd_hz: Optional[float]
    tach_rpm: Optional[float]
    note: str

    @property
    def vfd_rpm(self) -> Optional[float]:
        if self.vfd_hz is None:
            return None
        return self.vfd_hz * 60.0


def parse_float(value: str) -> Optional[float]:
    value = (value or "").strip()
    if not value:
        return None
    return float(value)


def load_rows(path: str) -> List[Row]:
    rows: List[Row] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        expected = {"S", "VFD_Hz", "Tach_RPM", "Note"}
        if not reader.fieldnames or not expected.issubset(set(reader.fieldnames)):
            raise ValueError("CSV 必須包含欄位: S,VFD_Hz,Tach_RPM,Note")

        for line in reader:
            s = parse_float(line.get("S", ""))
            if s is None:
                continue
            row = Row(
                s=s,
                vfd_hz=parse_float(line.get("VFD_Hz", "")),
                tach_rpm=parse_float(line.get("Tach_RPM", "")),
                note=(line.get("Note", "") or "").strip(),
            )
            rows.append(row)

    rows.sort(key=lambda item: item.s)
    return rows


def is_spinning(row: Row) -> bool:
    spinning_vfd = row.vfd_hz is not None and row.vfd_hz > 0.5
    spinning_tach = row.tach_rpm is not None and row.tach_rpm > 50.0
    return spinning_vfd or spinning_tach


def best_integer_scale(value: float, candidates=range(1, 17)) -> int:
    best_n = 1
    best_err = abs(value - 1.0)
    for n in candidates:
        err = abs(value - n)
        if err < best_err:
            best_n = n
            best_err = err
    return best_n


def ratio_analysis(rows: List[Row]) -> None:
    ratios: List[float] = []
    for row in rows:
        vfd_rpm = row.vfd_rpm
        if row.tach_rpm is None or vfd_rpm is None or vfd_rpm <= 0:
            continue
        ratios.append(row.tach_rpm / vfd_rpm)

    if not ratios:
        print("- 轉速倍率判讀: 資料不足（請至少填 2 筆 VFD_Hz 與 Tach_RPM）")
        return

    med = median(ratios)
    nearest = best_integer_scale(med)
    err = abs(med - nearest) / max(nearest, 1)

    print(f"- Tach/VFD 比值中位數: {med:.3f}")
    if 0.85 <= med <= 1.15:
        print("- 判讀: 轉速計倍率大致正常（接近 1x）")
    elif err <= 0.12:
        print(f"- 判讀: 轉速計疑似倍率錯誤，約為 {nearest}x")
        print("- 建議: 檢查轉速計每轉脈衝數、葉片數、反光貼紙數、極數設定")
    else:
        print("- 判讀: 比值不穩定，可能是量測方式或 VFD 讀值/轉速計讀值混雜")


def threshold_analysis(rows: List[Row], rpm_max: float, pwm_min: float) -> None:
    spin_rows = [row for row in rows if is_spinning(row)]
    if not spin_rows:
        print("- 啟轉門檻判讀: 尚未觀測到轉動，請確認主軸使能與 VFD 遠端控制")
        return

    first = spin_rows[0]
    suggested_pwm_min = (first.s / rpm_max) * 100.0

    print(f"- 首次可穩定轉動 S 值: {first.s:.1f}")
    print(f"- 由資料估算建議 $35: {suggested_pwm_min:.3f}%")

    delta = suggested_pwm_min - pwm_min
    if abs(delta) <= 0.6:
        print(f"- 判讀: 目前 $35={pwm_min:.3f}% 接近建議值")
    elif delta > 0:
        print(f"- 判讀: 目前 $35={pwm_min:.3f}% 偏低，建議提高約 {delta:.3f}%")
    else:
        print(f"- 判讀: 目前 $35={pwm_min:.3f}% 偏高，建議降低約 {abs(delta):.3f}%")


def monotonicity_analysis(rows: List[Row]) -> None:
    tach_rows = [row for row in rows if row.tach_rpm is not None]
    if len(tach_rows) < 3:
        print("- 線性化趨勢判讀: Tach 資料不足")
        return

    drops = []
    for prev, curr in zip(tach_rows, tach_rows[1:]):
        if curr.tach_rpm < prev.tach_rpm - 100:
            drops.append((prev, curr))

    if not drops:
        print("- 線性化趨勢判讀: Tach RPM 隨 S 單調上升（正常）")
    else:
        print(f"- 線性化趨勢判讀: 發現 {len(drops)} 段明顯逆向（可能量測抖動或分段配置不佳）")
        for prev, curr in drops[:3]:
            print(
                f"  - S{prev.s:.0f}->{curr.s:.0f}: {prev.tach_rpm:.0f}->{curr.tach_rpm:.0f} RPM"
            )


def command_tracking_analysis(rows: List[Row]) -> None:
    pairs = [(row.s, row.tach_rpm) for row in rows if row.tach_rpm is not None and row.tach_rpm > 0]
    if len(pairs) < 3:
        print("- 追蹤誤差判讀: Tach 資料不足")
        return

    errors = [abs(tach - s) / max(s, 1.0) for s, tach in pairs]
    med_err = median(errors)
    print(f"- |Tach-S|/S 中位誤差: {med_err * 100:.1f}%")

    if med_err <= 0.15:
        print("- 判讀: 指令追蹤良好")
    elif med_err <= 0.35:
        print("- 判讀: 指令追蹤中等，建議再收集中高轉速點重算一次")
    else:
        print("- 判讀: 指令追蹤偏差大，請先排除轉速計倍率問題再重算係數")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze spindle validation data.")
    parser.add_argument("csv_file", help="Path to CSV test data")
    parser.add_argument("--rpm-max", type=float, default=11867.5, help="Current $30 value")
    parser.add_argument("--pwm-min", type=float, default=4.167, help="Current $35 value in percent")
    args = parser.parse_args()

    rows = load_rows(args.csv_file)
    if not rows:
        raise SystemExit("CSV 沒有可用資料列")

    print("=== Spindle Validation Report ===")
    print(f"- 資料筆數: {len(rows)}")
    print(f"- 目前假設: $30={args.rpm_max}, $35={args.pwm_min}%")

    ratio_analysis(rows)
    threshold_analysis(rows, rpm_max=args.rpm_max, pwm_min=args.pwm_min)
    monotonicity_analysis(rows)
    command_tracking_analysis(rows)


if __name__ == "__main__":
    main()
