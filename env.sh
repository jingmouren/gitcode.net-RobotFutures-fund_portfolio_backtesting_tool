# python源更新为aliyun的源
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ 
# 安装中文字体
cp fonts/simhei.ttf /usr/share/fonts/&&apt install -y ttf-mscorefonts-installer fontconfig&&mkfontscale&&fc-cache