
git submodule status

git -C main/grbl  branch -r  
git -C main/grbl checkout e2d-master
git config -f .gitmodules submodule.main/grbl.branch e2d-master
git submodule sync --recursive
git submodule update --remote main/grbl

git -C main/networking  branch -r  
git config -f .gitmodules submodule.main/networking.branch e2d-update
git submodule sync --recursive
git submodule update --remote main/networking

git -C main/plugins  branch -r    
git -C main/plugins checkout e2d-update

git config -f .gitmodules submodule.main/plugins.branch e2d-update
git submodule sync --recursive
git submodule update --remote main/plugins

git -C main/grbl pull      # 拉 e2d-master 最新
git add main/grbl .gitmodules
