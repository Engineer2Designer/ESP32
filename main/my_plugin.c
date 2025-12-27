/*
  my_plugin.c - User plugin initialization

  Part of grblHAL

  Copyright (c) 2025 E2D

  grblHAL is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  grblHAL is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with grblHAL. If not, see <http://www.gnu.org/licenses/>.
*/

#include "driver.h"

// E2D ATC Plugin
#if E2D_ATC_ENABLE
#include "plugins/Plugin-e2d_atc/e2d_atc.h"
#endif

// Plugin OLED Display
#if DISPLAY_ENABLE == 9
extern void plugin_display_init(void);
#endif

// Initialize user plugins
void my_plugin_init (void)
{
#if E2D_ATC_ENABLE
    e2d_atc_init();
#endif

#if DISPLAY_ENABLE == 9
    plugin_display_init();
#endif

    // Add more user plugins here as needed
}
