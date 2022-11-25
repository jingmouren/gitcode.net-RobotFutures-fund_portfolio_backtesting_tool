**1024云IDE应用挑战赛地址：[https://gitcode.net/cloud-ide/1024](https://gitcode.net/cloud-ide/1024)**
 
**获奖名单：[https://gitcode.net/cloud-ide/1024/-/blob/main/%E8%8E%B7%E5%A5%96%E5%90%8D%E5%8D%95%E5%85%AC%E5%B8%83.md](https://gitcode.net/cloud-ide/1024/-/blob/main/%E8%8E%B7%E5%A5%96%E5%90%8D%E5%8D%95%E5%85%AC%E5%B8%83.md)**

![image-20221125210102904](https://robot-futures-oss-zone.oss-cn-hangzhou.aliyuncs.com/imgs/202211252101993.png)

# 1. 项目概述

**本项目为基金组合定投回测工具，不构成投资建议！**

项目是博主想实现躺赢的基金组合投资工具^ ^。
博主的基金投资理念是指数基金长期价值定投，买大盘指数，分散投资，优先保住本金。

![](https://robot-futures-oss-zone.oss-cn-hangzhou.aliyuncs.com/imgs/202211061422564.png))

## 1.1 分散投资
- 分散到不同的品类：例如沪深300、中证500、创业板；
    - 像沪深300是沪深股市表现最好的300家企业，代表了中国经济，稳定，但是收益可能相对低一些，可以多配置一些；
    - 中证500是中国证券市场表现最好的500家企业，范围更广一些；
    - 创业板是中国股市创业型企业，冲劲大，代表中国经济未来的新势力，风险高，收益也高，可以少配置一些
    - 黄金指数是跟踪实物黄金价格的基金，俗话说：乱世买黄金，盛世买股票，股市表现不好的时候，黄金可能表现好
    - 债权指数是跟踪国债的基金，是组合基金的不动基石，在其他价值标的表现不好的时候，也不至于整体表现太差；
- 分散到不同的国家：中国、美国(标普500、纳斯达克100)等
    - 标普500，美国市场表现最好的500家企业
    - 纳斯达克100，科技企业大多在纳斯达克上市，价值你知道的
- 目前博主的基金组合配比大致为
    - 沪深300 25%
    - 中证500 15%
    - 创业板  10%
    - 黄金  10%
    - 债权 20%
    - 标普500 15%
    - 纳斯达克100 5%

    博主没有测试更多份额比例，可以自行测试。

    还可以测试更多组合，例如基金组合的典型组合：永久组合、60/40组合、斯文森组合、全天候组合等。
    

## 1.2 定期再平衡
基金组合创建时不同的基金会有不同的份额，再运行一段时间后，份额会发生变化，有点基金可能涨了很多，有点基金可能会跌了一些，有的人买基金不挣钱的原因是什么，不会卖，涨的钱又流出去了。
股市是有周期的，涨涨跌跌，潮起潮落，通过定期再平衡，将运行一段时间的基金份额重新配置为初始份额比例，变相的实现了高卖低买的目的，实现了削尖平谷的目的，挣取更多超额收益。

再平衡周期建议1年操作一次，这样可以减少费用。

# 2. 使用指南
## 2.1 启动运行
### 2.1.1 方式一
直接打开CSDN 云IDE自动运行：[https://idegitcode.net/RobotFutures/1024](https://idegitcode.net/RobotFutures/1024)

### 2.1.2 方式二
- 从gitcode下载源码
```
git clone https://gitcode.net/RobotFutures/1024.git
```

- 启动运行
```
pip install -r requirements.txt&&python fund_portfolio_backtesting_tool.py
```

## 2.2 目录结构
```
├── CHANGELOG.MD                        # 修订记录
├── README.md                           # 使用文档
├── fund_fee_list.csv                   # 爬取的公募基金交易费用
├── fund_portfolio_backtesting_tool.py  # 基金组合回测工具程序
├── log.txt                             # 日志输出
├── package.json    
├── preview.yml                         # 自动启动运行脚本配置
├── requirements.txt                    # 项目所需库
├── src
├── 公募基金概要数据.csv                 # 下载的公募基金概要数据，包含交易费用
├── 回测结果                             # 回测计算结果
    └── 2022-11-06_01-23-39             # 回测时间
        ├── fund_portfolio_result.csv   # 基金组合清单及份额占比
        ├── fund_portfolio_trend.png    # 基金组合与沪深300对比
        ├── 沪深300基金参考.csv          # 沪深300参考基金历史数据
        └── 自选组合基金回测数据.csv     # 基金组合回测历史数据
├── 数据可靠性验证                       # 使用EXCEL验证组合基金复权净值的数据可靠性
    ├── 数据可靠性验证.xlsx             # 数据可靠性数据验证文档，使用EXCEL函数来实现
    ├── fund_portfolio_result.csv       # 基金组合份额数据
    └── 自选组合基金回测数据.csv        # 基金组合回测历史数据
├── 基金关键字筛选结果                   # 大盘基金关键字及策略筛选结果
├── 基金组合筛选结果列表                 # 筛选结果基金性能指标
    ├── fund_portfolio_result.csv       # 基金组合清单及份额占比
    ├── fund_portfolio_trend.png        # 基金组合与沪深300对比
    ├── 沪深300基金参考.csv              # 沪深300参考基金历史数据
    └── 自选组合基金回测数据.csv        # 基金组合回测历史数据
├── 累计净值趋势                         # 下载的公募基金累计净值历史数据       
└── 累计回报趋势                        # 下载的公募基金累计回报历史数据    
```

## 2.3 回测结果展示
- 回测结果可视化展示
![](https://robot-futures-oss-zone.oss-cn-hangzhou.aliyuncs.com/imgs/202211061422564.png))

- 自选组合基金
```
Unnamed: 0,code,years,withdrawal,annual_return,total_return,sharp,calmar,volatility,name,type,scale,m_fee,c_fee,sale_fee,sub_fee,total_fee,share
16.0,002670,6.11,27.34,6.74,37.02,0.46,12.9743,19.4,万家沪深300指数增强A,股票指数,6.34,1.0,0.12,0.0,0.1,1.22,0.25
97.0,502000,7.55,29.38,9.81,57.14,0.62,18.3793,20.16,西部利得中证500指数增强A,股票指数,5.08,1.0,0.2,0.0,0.1,1.3,0.15
3.0,001879,5.42,37.64,12.36,75.57,0.59,16.5217,26.3,长城创业板指数增强A,股票指数,6.58,1.0,0.15,0.0,0.15,1.3,0.1
4.0,002610,6.43,20.27,7.04,38.89,0.65,15.5788,12.22,博时黄金ETF联接A,联接基金,8.27,0.5,0.1,0.0,0.06,0.66,0.1
134.0,002864,6.38,0.61,3.38,17.41,10.81,224.7164,0.32,广发安泽短债债券A,债券型,28.99,0.3,0.1,0.0,0.04,0.4399999999999999,0.2
4.0,050025,10.39,31.17,11.3,67.75,0.65,17.4237,20.85,博时标普500ETF联接A,QDII-指数,8.87,0.6,0.25,0.0,0.12,0.97,0.15
5.0,161130,5.37,28.32,13.13,81.43,0.66,23.5765,25.47,易方达纳斯达克100人民币,QDII-指数,7.36,0.8,0.25,0.0,0.12,1.17,0.05

```

- 数据可靠性验证

使用EXCEL按照组合基金份额占比，计算基金组合组合复权净值，测试结果如下（详情见【数据可靠性验证】目录）：

**EXCEL计算基金组合复权净值**

![image-20221106234134442](https://robot-futures-oss-zone.oss-cn-hangzhou.aliyuncs.com/imgs/202211062341074.png)

**fund_portfolio_backtestng_tool回测工具计算基金组合复权净值**

![image-20221106234413472](https://robot-futures-oss-zone.oss-cn-hangzhou.aliyuncs.com/imgs/202211062344541.png)

可以看到两者的数据是一致的，因此工具的数据可靠性是可以保证的。

# 3. 自建组合
找到代码的这个位置
```
if __name__ == "__main__":
    pd.set_option('display.max_rows', 1000)
    pd.set_option('display.max_columns', 10)

    # 获得公募基金基础数据(这里不用管，执行即可)
    df_base = get_fund_base_info()

    # 大盘基金筛选(这里就是基金筛选策略)
    # 筛选策略是关键字、最大历史回测，基金成立时间、基金最小规模、基金最大允许的交易费率
    # 可支持的关键字很多，从基金的分类通用关键字即可，例如半导体、新能源、量化等
    df_kpi_csi300 = get_fund_rank(fund_list=df_base, keywords='沪深300', max_withdrawal=60.0, establish_year=5, start='2018-01-01', end='2022-10-31')
    df_kpi_csi500 = get_fund_rank(df_base, '中证500', 50.0, 5, '2018-01-01', '2022-10-31')
    df_kpi_gem = get_fund_rank(df_base, '创业板', 50.0, 5, '2018-01-01', '2022-10-31')
    df_kpi_gold = get_fund_rank(df_base, '黄金', 50.0, 5, '2018-01-01', '2022-10-31')
    df_kpi_bond = get_fund_rank(df_base, '债', 30.0, 5, '2018-01-01', '2022-10-31')
    df_kpi_sp500 = get_fund_rank(df_base, '标普500', 50.0, 5, '2018-01-01', '2022-10-31')
    df_kpi_nasda = get_fund_rank(df_base, '纳斯达克', 50.0, 5, '2018-01-01', '2022-10-31')

    # 定投基金组合回测
    fund_portfolio_backtesting(
        # 这里填写上面获得基金分类数据集
        fund_kinds_list = [df_kpi_csi300, df_kpi_csi500, df_kpi_gem, df_kpi_gold, df_kpi_bond, df_kpi_sp500, df_kpi_nasda],
        # 这里配置对应上面的基金份额
        fund_share_cfg = [0.25, 0.15, 0.10, 0.10, 0.20, 0.15, 0.05],
        # 这里填写回测起始时间和结束时间，参考跟踪基金
        start_date = '2018-01-01', end_date = '2022-10-31', fund_id_ref = '160706'
    )
```

# 4. 联系我
关注作者更多消息，请订阅博客[https://blog.csdn.net/RobotFutures?spm=1010.2135.3001.5343](https://blog.csdn.net/RobotFutures?spm=1010.2135.3001.5343)

- 基金组合价值定投技术交流请联系博主(请备注:基金技术交流)

![](weixin.png)

