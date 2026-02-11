
git submodule status (檢查 submodule 狀態)

git -C main/grbl  branch -r  
git -C main/grbl checkout DLC32_V1.2
git config -f .gitmodules submodule.main/grbl.branch DLC32_V1.2
git submodule sync --recursive
git submodule update --remote main/grbl

git -C main/networking  branch -r
git -C main/networking checkout DLC32_V1.2 
git config -f .gitmodules submodule.main/networking.branch e2d-update
git submodule sync --recursive
git submodule update --remote main/networking

git -C main/plugins  branch -r    
git -C main/plugins checkout e2d-update
git config -f .gitmodules submodule.main/plugins.branch DLC32_V1.2
git submodule sync --recursive
git submodule update --remote main/plugins

git submodule update --init --recursive (初始化並更新所有子模組)