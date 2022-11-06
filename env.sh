# python源更新为aliyun的源
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ 
# 安装中文字体
cp fonts/simhei.ttf /usr/share/fonts/&&apt install -y ttf-mscorefonts-installer fontconfig&&mkfontscale&&fc-cache
# 修改时区为东八区
ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime