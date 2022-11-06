"""基金定投组合筛选工具

notes:
    1. 未计算赎回费用：以长期定投为目标，因此赎回费可忽略。
    2. 以嘉实沪深300ETF联接A(160706)基金为沪深300跟踪基金，其跟踪误差率为0.07%
"""

import akshare as ak
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.pyplot import MultipleLocator
import matplotlib.dates as mdate
import requests
from bs4 import BeautifulSoup
import datetime
import time
import math
import os
import re
import random
from decimal import Decimal
import matplotlib.ticker as ticker
import matplotlib.dates as mdates

DIR_CUMULATIVE_NET_VALUE_TREND = '累计净值趋势'
DIR_CUMULATIVE_RETURN_TREND = '累计回报趋势'
DIR_FUND_FILTER_RESULT_SORT_DATA = '基金组合筛选结果列表'
DIR_FUND_FILTER_DATA_BY_KEYWORD = '基金关键字筛选结果'
DIR_OUTPUT = "回测结果"

# 无风险年化收益率%
risk_free_annual_return_ratio = 0.0275

# 每年交易日天数
trading_days_per_year = 250

# user_agent列表
user_agent_list = [
  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER',
  'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)',
  'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 SE 2.X MetaSr 1.0',
  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.4.3.4000 Chrome/30.0.1599.101 Safari/537.36',
  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 UBrowser/4.0.3214.0 Safari/537.36'
]
# referer列表
referer_list = [
  'http://fund.eastmoney.com/110022.html',
  'http://fund.eastmoney.com/110023.html',
  'http://fund.eastmoney.com/110024.html',
  'http://fund.eastmoney.com/110025.html'
]

# 获取一个随机user_agent和Referer
header = {'User-Agent': random.choice(user_agent_list),
     'Referer': random.choice(referer_list)
}

# 获得字符串中的整数
def get_decimal(x):
    return ''.join(re.findall(r"\d+\.?\d*", ''.join(x)))
    # try:
    #     return float(''.join(re.findall(r"\d+\.?\d*", x)))
    # except:
    #     return re.findall(r"\d+\.?\d*", x)
    # return float(''.join(re.findall(r"\d+\.?\d*", x)))

# 获得指定后缀字符串中的整数
def get_decimal_suffix(x, suffix):
    return get_decimal(re.findall(r"\d+\.?\d*"+suffix, ''.join(x)))

# 日志调试
def log(x):
    file_handle = open('log.txt', mode='a', encoding='utf-8')
    file_handle.write(f"{time.strftime('%Y-%m-%d', time.localtime())}:{x}")
    file_handle.close()

# 获得基金概要数据
def get_all_fund_outline():
    if not os.path.exists('公募基金概要数据.csv'):
        df1 = ak.fund_name_em()
        df1 = df1[['基金代码', '拼音缩写', '基金类型']]
        df2 = ak.fund_open_fund_daily_em()
        df = pd.merge(df1, df2, on='基金代码')
        df.set_index(df['基金代码'])
        df.to_csv('公募基金概要数据.csv', encoding='utf_8_sig',index=None)

        print(df)
    else:
        df = pd.read_csv('公募基金概要数据.csv', dtype=object)

    return df

#
def get_all_open_fund_daily():
    """获得公募基金每日净值

    Returns:
        DataFrame: 公募基金当日净值数据
    """
    if not os.path.exists('open_fund_daily.csv'):
        fund_em_fund_name_df = ak.fund_open_fund_daily_em()
        fund_em_fund_name_df.set_index(fund_em_fund_name_df['基金代码'])
        fund_em_fund_name_df.to_csv('fund_em_open_fund_daily.csv', encoding='utf_8_sig',index=None)
    else:
        fund_em_fund_name_df = pd.read_csv('fund_em_open_fund_daily.csv', dtype=object)

    return fund_em_fund_name_df

def query_fund_by_fundname_keyword(df, fundname_keyword):
    """根据关键字过滤基金列表

    Args:
        df (DataFrame): 公募基金列表
        fundname_keyword (str): 过滤关键字

    Returns:
        _type_: _description_
    """
    if not os.path.exists(DIR_FUND_FILTER_DATA_BY_KEYWORD):
        os.makedirs(DIR_FUND_FILTER_DATA_BY_KEYWORD)

    df_query = df[df['基金简称'].str.contains(fundname_keyword)]
    df_query.set_index(df_query['基金代码'])
    df_query.to_csv(f'{DIR_FUND_FILTER_DATA_BY_KEYWORD}/{fundname_keyword}.csv', encoding='utf_8_sig',index=None)

    return df_query

# 获得分红数据
def get_fund_dividend_by_id(dir, fund_id):
    """查询指定基金编号分红数据

    Args:
        dir (str): 分红数据目录
        fund_id (str): 基金编号

    Returns:
        DataFrame: 分红数据
    """
    filename = dir + '/%s' % (fund_id) + '-dividend.csv'
    try:
        if not os.path.exists(filename):
            df = ak.fund_open_fund_info_em(fund=fund_id, indicator="分红送配详情")
            print(df)
            for i in np.arange(0, df.shape[0]):
                df.iloc[i]['每份分红'] = get_decimal(df.iloc[i]['每份分红'])

            df.to_csv(filename, encoding='utf_8_sig', index=None)
        else:
            df = pd.read_csv(filename, dtype=object)

        return df
    except:
        return NULL


def query_last_dividend_before_date(df, cur_date):
    """获得最近一次分红

    Args:
        df (DataFrame): 单支基金历史数据
        cur_date (str): 指定日期

    Returns:
        _type_: 最近一次分红
    """
    try:
        dividend = '0.0'
        # 查询最近一次的分红数据，满足条件反馈分红
        for i in np.arange(0, df.shape[0]):
            if str(cur_date) > df.iloc[df.shape[0] - 1 - i]['分红发放日']:
                # print('Index:', df.shape[0] - 1 - i)
                dividend = df.iloc[df.shape[0] - 1 - i]['每份分红']

        # print("日期:%s"%cur_date, "分红%s"%dividend)

        return dividend
    except:
        return '0.0'

def getLastday(end_date): 
    """获得指定日期前一天的日期

    Args:
        end_date (str): 指定日期

    Returns:
        last_day: 指定日期前一天的日期str
    """
    # today=datetime.date.today()
    day = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
    oneday=datetime.timedelta(days=1) 
    last_day = day-oneday  
    return last_day

# 获得指定基金历史数据
def get_fund_his_by_id(fund_id, dir, end):
    """加载指定基金编号历史数据

    Args:
        fund_id (str): 基金编号
        dir (str): 基金历史存放路径
        end (str): 截止时间

    Returns:
        DataFrame: 基金历史数据
    """
    filename = dir + '/%s'%(fund_id) + '.csv'
    # print(filename)

    if not os.path.exists(dir):
        os.makedirs(dir)
        
    try:
        if not os.path.exists(filename):
            print(f"基金{fund_id}数据不存在，加载中...")
            df_total_net_value_trend = ak.fund_open_fund_info_em(fund=fund_id, indicator='累计净值走势')
            df_unit_net_value_trend = ak.fund_open_fund_info_em(fund=fund_id, indicator="单位净值走势")
            fund_em_info_df = pd.merge(df_total_net_value_trend, df_unit_net_value_trend, on='净值日期')
            fund_em_info_df.set_index(fund_em_info_df['净值日期'])

            if not isinstance(fund_em_info_df['日增长率'], float):
                fund_em_info_df['日增长率'] = fund_em_info_df['日增长率'].astype(float)

            df_dividend = get_fund_dividend_by_id(dir, fund_id)

            # 复权列表
            red_net_value_list = []
            last_red_net_value = 0.0

            # print(fund_em_info_df)
            # print(f"fund_em_info_df.shape:{fund_em_info_df.shape}")

            # 复权净值计算
            for i in np.arange(0, fund_em_info_df.shape[0]):
                dividend = float(query_last_dividend_before_date(df_dividend, fund_em_info_df.iloc[i]['净值日期']))
                # print(dividend)

                if dividend > 0.0:
                    try:
                        last_red_net_value = float(last_red_net_value * (1 + fund_em_info_df.iloc[i]['日增长率'] / 100))
                        red_net_value_list.append(last_red_net_value)

                        # print('date:',fund_em_info_df.iloc[i]['净值日期'], '单位净值:', fund_em_info_df.iloc[i]['单位净值'], \
                        #       '日增长率:', fund_em_info_df.iloc[i]['日增长率'], '累计净值', fund_em_info_df.iloc[i]['累计净值'])
                    except:
                        print(fund_id, '日增长率数据异常:', fund_em_info_df.iloc[i]['日增长率'])
                        return ''
                else:
                    try:
                        last_red_net_value = float(fund_em_info_df.iloc[i]['累计净值'])
                        red_net_value_list.append(last_red_net_value)
                    except:
                        print(fund_id, '累计净值数据异常:', fund_em_info_df.iloc[i]['累计净值'])
                        return ''
            fund_em_info_df['复权净值'] = red_net_value_list

            # print(fund_em_info_df)
            fund_em_info_df.to_csv(filename, encoding='utf_8_sig',index=None)
        else:
            fund_em_info_df = pd.read_csv(filename, dtype=object)
            bottom = fund_em_info_df.tail(1)
            # print(bottom)

            # print(fund_em_info_df)

            # now = time.strftime('%Y-%m-%d', time.localtime())
            yesterday = getLastday(end)
            # print(type(yesterday), str(yesterday), bottom.iloc[0]['净值日期'])
            if str(bottom.iloc[0]['净值日期']) < str(yesterday):
                log(f"基金{fund_id}数据不是最新的，最近日期{bottom.iloc[0]['净值日期']}\n")
                print(f"基金{fund_id}数据不是最新的，最近日期{bottom.iloc[0]['净值日期']}, 更新至最新...")
                df_total_net_value_trend = ak.fund_open_fund_info_em(fund=fund_id, indicator='累计净值走势')
                df_unit_net_value_trend = ak.fund_open_fund_info_em(fund=fund_id, indicator="单位净值走势")
                fund_em_info_df = pd.merge(df_total_net_value_trend, df_unit_net_value_trend, on='净值日期')
                fund_em_info_df.set_index(fund_em_info_df['净值日期'])

                if not isinstance(fund_em_info_df['日增长率'], float):
                    fund_em_info_df['日增长率'] = fund_em_info_df['日增长率'].astype(float)

                df_dividend = get_fund_dividend_by_id(dir, fund_id)

                # 复权列表
                red_net_value_list = []
                last_red_net_value = 0.0

                # print(fund_em_info_df)
                # print(f"fund_em_info_df.shape:{fund_em_info_df.shape}")

                # 复权净值计算
                for i in np.arange(0, fund_em_info_df.shape[0]):
                    dividend = float(query_last_dividend_before_date(df_dividend, fund_em_info_df.iloc[i]['净值日期']))
                    # print(dividend)

                    if dividend > 0.0:
                        try:
                            last_red_net_value = float(last_red_net_value * (1 + fund_em_info_df.iloc[i]['日增长率'] / 100))
                            red_net_value_list.append(last_red_net_value)

                            # print('date:',fund_em_info_df.iloc[i]['净值日期'], '单位净值:', fund_em_info_df.iloc[i]['单位净值'], \
                            #       '日增长率:', fund_em_info_df.iloc[i]['日增长率'], '累计净值', fund_em_info_df.iloc[i]['累计净值'])
                        except:
                            print(fund_id, '日增长率数据异常:', fund_em_info_df.iloc[i]['日增长率'])
                            return ''
                    else:
                        try:
                            last_red_net_value = float(fund_em_info_df.iloc[i]['累计净值'])
                            red_net_value_list.append(last_red_net_value)
                        except:
                            print(fund_id, '累计净值数据异常:', fund_em_info_df.iloc[i]['累计净值'])
                            return ''
                fund_em_info_df['复权净值'] = red_net_value_list

                fund_em_info_df_wr = fund_em_info_df[fund_em_info_df['净值日期'].astype(str) > str(bottom.iloc[0]['净值日期'])]
                fund_em_info_df_wr.to_csv(filename, encoding='utf_8_sig',index=None, mode='a', header=False)

            fund_em_info_df.set_index(fund_em_info_df['净值日期'])
    except Exception as e:
        print(f"错误信息：{e}")

    return fund_em_info_df


def draw_cumulative_net_value_trend(x, y, ref, dir_output):
    """绘制基金净值走势

    Args:
        x (list): 日期时间
        y (list): 基金组合累计净值
        ref (list): 沪深300参考基金累计净值
    """
    # windows配置SimHei，Ubuntu配置WenQuanYi Micro Hei
    plt.rcParams["font.sans-serif"]=["SimHei"] #设置字体    
    plt.rcParams["axes.unicode_minus"]=False #该语句解决图像中的“-”负号的乱码问题

    fig, ax = plt.subplots(figsize=(16, 9))

    ax.set_xlabel("时间")
    ax.set_ylabel("基金累计净值")
    ax.set_title("基金走势图")
    # print(x, y)

    ax.plot(x, y, c='red', label='自选基金组合回测数据', alpha=0.6)
    ax.plot(x, ref, c='green', label='沪深300', alpha=0.6)

    # ax.set_xticklabels(labels=x[::90], rotation=45)  # 旋转45度
    tick_spacing = 90
    ax.xaxis.set_major_locator(ticker.MultipleLocator(tick_spacing))

    ax.legend()
    plt.xticks(rotation=45)
    plt.savefig(f"{dir_output}/fund_portfolio_trend.png")
    plt.show()

def calc_fund_established_time(df):
    """计算基金成立时间

    Args:
        df (DataFrame): 单支基金历史数据

    Returns:
        float: 基金成立年数
    """
    # print(df.dtypes)
    # print(df.iloc[-1, 0], df.iloc[0, 0], df.iloc[-1, 0]-df.iloc[0, 0])
    established_time = (df.iloc[-1, 0] - df.iloc[0, 0]).days/365
    return established_time

# 
def calc_fund_drawdown(fund_df, start='2010-01-01', end='2200-01-01'):
    """计算基金最大回撤

    Args:
        fund_df (DataFrame): 单支基金历史数据
        start (str, optional): 起始时间. Defaults to '2010-01-01'.
        end (str, optional): 结束时间. Defaults to '2200-01-01'.

    Returns:
        float: 时间区间最大历史回测、回测起始时间、回测结束时间
    """
    df = fund_df[['净值日期', '复权净值']].copy()
    df['净值日期'] = pd.to_datetime(df['净值日期'])

    st = df['净值日期'] >= start
    et = df['净值日期'] <= end
    res = st == et
    df = df[res]

    df['max2here'] = df['复权净值'].expanding().max()
    df['dd2here']  = df['复权净值']/df['max2here']

    end_date, remains = tuple(df.sort_values(by=['dd2here']).iloc[0][['净值日期', 'dd2here']])

    # 计算最大回撤开始时间
    start_date = df[df['净值日期']<=end_date].sort_values(by='复权净值', ascending=False).iloc[0]['净值日期']

    drawdown = round((1-remains)*100, 2)
    print('最大回撤 (%):', drawdown)
    print('最大回撤开始时间:', start_date)
    print('最大回撤结束时间:', end_date)

    return drawdown, start_date, end_date

# 计算基金年华回报率
def cal_fund_annual_return(fund_df, start='2010-01-01', end='2200-01-01'):
    """计算基金年华回报率

    Args:
        fund_df (DataFrame): 单支基金历史数据
        start (str, optional): 起始时间. Defaults to '2010-01-01'.
        end (str, optional): 结束时间. Defaults to '2200-01-01'.

    Returns:
        float: 年化回报率
    """
    df = fund_df[['净值日期', '复权净值']].copy()

    st = df['净值日期'] >= start
    et = df['净值日期'] <= end
    res = st == et
    df = df[res]

    total_return = round(((df.iloc[-1, 1] / df.iloc[0, 1]) - 1)*100, 2)
    # df = df.fillna(0.0)
    # print(df)

    years = round(calc_fund_established_time(df), 2)
    # print('分析周期:%f years'%years)

    # 计算
    # print("最新累计收益率:%f, "%df.iloc[-1, 4] + '初始累计收益率:%f'%df.iloc[0, 4])
    if years >= 1:
        annualized_returns = (df.iloc[-1, 1] / df.iloc[0, 1])**(1/years) - 1
    else:
        annualized_returns = (df.iloc[-1, 1] / df.iloc[0, 1]) - 1

    annualized_returns = annualized_returns*100

    print('annualized_returns:%f'%annualized_returns + '%')

    return annualized_returns, total_return;

def cal_fund_sharpe_ratio(fund_df, withdrawal, start='1970-01-01', end='2200-01-01'):
    """计算基金夏普比率

    Args:
        fund_df (DataFrame): 计算单支基金夏普比率
        withdrawal (float): 时间范围内的最大回撤
        start (str, optional): 起始时间. Defaults to '1970-01-01'.
        end (str, optional): 结束时间. Defaults to '2200-01-01'.

    Returns:
        float: 夏普比率，卡玛比率
    """
    df = fund_df[['净值日期', '日增长率']].copy()

    st = df['净值日期'] >= start
    et = df['净值日期'] <= end
    res = st == et
    df = df[res]
    # print(df)

    # 计算日收益率的均值
    daily_return_ratio_average = np.mean(df['日增长率'].astype(float))*100
    # print('daily_return_ratio_average:%f'%daily_return_ratio_average)

    # 计算收益率的标准方差
    return_ratio_std = df['日增长率'].astype(float).std()

    # 计算无风险日收益率
    daily_risk_free_return_ratio = (((1 + risk_free_annual_return_ratio)**(1/365)) - 1) * 100
    # print('daily_risk_free_return_ratio:%f' % daily_risk_free_return_ratio)

    # 计算夏普比率
    try:
        fund_sharpe_ratio = (daily_return_ratio_average - daily_risk_free_return_ratio) / return_ratio_std * math.sqrt(trading_days_per_year) / 100
    except:
        fund_sharpe_ratio = 0.0

    # 计算卡玛比率
    try:
        fund_calmar_ratio = (daily_return_ratio_average - daily_risk_free_return_ratio) / withdrawal * 100
    except:
        fund_calmar_ratio = 0.0

    print('sharpe_ratio:%f' % fund_sharpe_ratio + ', calmar_ratio:%f' % fund_calmar_ratio)
    return fund_sharpe_ratio, fund_calmar_ratio

# 计算基金波动
def calc_fund_volatility(df_fund, start='2010-01-01', end='2200-01-01'):
    """计算基金波动性指标

    Args:
        df_fund (DataFrame): 单支基金的历史数据
        start (str, optional): 计算起始时间. Defaults to '2010-01-01'.
        end (str, optional): 计算结束时间. Defaults to '2200-01-01'.

    Returns:
        float: 波动率
    """
    # difflntotal = []

    df = df_fund[['净值日期', '复权净值', '上一交易日复权净值']].copy()
    # df['上一次累计净值'] = df['累计净值'].shift(1)

    st = df['净值日期'] >= start
    et = df['净值日期'] <= end
    res = st == et
    df = df[res]

    # days = df.shape[0]
    # print(days)

    df['价格自然对数差'] = np.log(df['复权净值']) - np.log(df['上一交易日复权净值'])
    volitality = np.std(df['价格自然对数差']) * 100 * math.sqrt(trading_days_per_year)

    print('volitality:%f'%volitality)

    return volitality

# 计算基金kpi
def calc_fund_kpi(fund_id, df_cumulative_net_value_trend, start='2010-01-01', end='2200-01-01'):
    """计算单支基金的性能指标

    Args:
        fund_id (str): 基金编号
        df_cumulative_net_value_trend (DataFrame): 累计净收益走势
        start (str, optional): 计算kpi起始时间. Defaults to '2010-01-01'.
        end (str, optional): 计算kpi结束时间. Defaults to '2200-01-01'.

    Returns:
        _type_: _description_
    """
    dict_select = {
        'code': fund_id,  # 基金代码
        'years': '',        # 成立时间
        'withdrawal': '',   # 最大回撤
        'annual_return': '',  # 年化收益率
        'total_return': '',  # 累计收益率
        'sharp': '',        # 夏普比率
        'calmar': '',       # 卡玛比率
        'volatility': '',   # 波动率
    }

    df = df_cumulative_net_value_trend[['净值日期', '复权净值', '日增长率']].copy()

    # 生成上一个交易日累计净值
    df['上一交易日复权净值'] = df['复权净值'].shift(1)

    # 数据格式转换
    df['净值日期'] = pd.to_datetime(df['净值日期'])
    df['复权净值'] = df['复权净值'].astype(float)
    df['上一交易日复权净值'] = df['上一交易日复权净值'].astype(float)

    # 计算成立时间
    years = calc_fund_established_time(df)
    dict_select['years'] = round(years, 2)
    print('基金[%s'%fund_id + ']成立时间:%d'%(int(years)) + '年%d'%((years-int(years))*365) + '天')

    # 计算最大回撤
    withdrawal, start_date, end_date = calc_fund_drawdown(df, start, end)
    dict_select['withdrawal'] = round(withdrawal, 2)
    # 计算年化收益
    annual_return, total_return = cal_fund_annual_return(df, start, end)
    dict_select['annual_return'] = round(annual_return, 2)
    dict_select['total_return'] = round(total_return, 2)

    # 计算夏普比率
    sharpe_ratio, calmar_ratio = cal_fund_sharpe_ratio(df, withdrawal, start, end)
    dict_select['sharp'] = round(sharpe_ratio, 2)
    dict_select['calmar'] = round(calmar_ratio, 4)

    # 计算波动率
    volatility = calc_fund_volatility(df, start, end)
    dict_select['volatility'] = round(volatility, 2)
    # calc_fund_volatility(df)

    print(dict_select)
    # df_kpi = pd.DataFrame(data=dict_select, columns=dict_select.keys())
    # print(df_kpi)

    return dict_select

# user_agent列表
user_agent_list = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)',
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 SE 2.X MetaSr 1.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.4.3.4000 Chrome/30.0.1599.101 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 UBrowser/4.0.3214.0 Safari/537.36'
]

# referer列表
referer_list = [
    'http://fund.eastmoney.com/110022.html',
    'http://fund.eastmoney.com/110023.html',
    'http://fund.eastmoney.com/',
    'http://fund.eastmoney.com/110025.html'
]

def get_url(baseUrl):
    """爬取网页基金数据

    Args:
        baseUrl (str): 爬取网址

    Returns:
        str: 网页文本数据
    """
    # 获取一个随机user_agent和Referer
    headers = {'User-Agent': random.choice(user_agent_list), 'Referer': random.choice(referer_list)}
    try:
        resp = requests.get(baseUrl, headers=headers)
        # print(resp.status_code)
        if resp.status_code == 200:
            # print(resp.content)
            return resp.text
        print("没有爬取到相应的内容")
        return None
    except:
        print("没有爬取到相应的内容")
        return None

def get_fund_fee(code):
    """获得单支基金费用

    Args:
        code (str): 基金编号

    Returns:
        dict: 单支基金费用
    """
    dict_select = {
        '基金代码': code,  # 基金代码
        'scale': '',  # 基金规模
        'm_fee': '',  # 管理费
        'c_fee': '',  # 托管费
        'sale_fee': '',  # 销售费用
        'sub_fee': '',  # 申购费<50W
        # 'buy_fee_less_than_100': '',  # 申购费<100W
        # 'buy_fee_more_than_100': '',  # 申购费>=100W
    }

    url = 'http://fundf10.eastmoney.com/jjfl_%s' % code + '.html'
    html = get_url(url)
    soup = BeautifulSoup(html, 'html.parser')
    # log(soup.prettify())

    target = ''
    for co in soup.find_all(['span', 'td', 'span', 'label']):
        # log('target%s' % target)
        # log('co.text:%s' % co.text)
        if target != '':
            # '''dict_select[target] = co.text.encode('utf-8')'''
            dict_select[target] = co.text
            if target == 'sale_fee':
                break
            target = ''

        if co.text.find(u'资产规模') >= 0:
            target = 'scale'
        elif co.text == u'管理费率':
            target = 'm_fee'
        elif co.text == u'托管费率':
            target = 'c_fee'
        elif co.text == u'销售服务费率':
            target = 'sale_fee'

    # print(dict_select)

    try:
        dict_select['scale'] = float(get_decimal_suffix(dict_select['scale'], '亿元'))
        if dict_select['scale'] == '':
            dict_select['scale'] = 0.0
    except:
        dict_select['scale'] = 0.0

    try:
        dict_select['m_fee'] = float(get_decimal(dict_select['m_fee']))
        if dict_select['m_fee'] == '':
            dict_select['m_fee'] = 0.0
    except:
        dict_select['m_fee'] = 0.0

    try:
        dict_select['c_fee'] = float(get_decimal(dict_select['c_fee']))
        if dict_select['c_fee'] == '':
            dict_select['c_fee'] = 0.0
    except:
        dict_select['c_fee'] = 0.0

    try:
        dict_select['sale_fee'] = float(get_decimal(dict_select['sale_fee']))
        if dict_select['sale_fee'] == '':
            dict_select['sale_fee'] = 0.0
    except:
        dict_select['sale_fee'] = 0.0

    print(dict_select)
    return dict_select

def get_fund_fee_list(df):
    """获得基金费用列表

    Args:
        df (_type_): 基金清单

    Returns:
        DataFrame: 基金费用
    """
    err_count = 0
    fee_list = []
    filename = 'fund_fee_list.csv'
    filename_bak = 'fund_fee_list-bak.csv'
    # print(filename)

    if not os.path.exists(filename):
        for i in np.arange(0, df.shape[0]):
            # try:
            print('基金编码[%s'%(df.iloc[i]['基金代码']) + ']正在读取费用...')
            dict_item = get_fund_fee(df.iloc[i]['基金代码'])
            dict_item['sub_fee'] = df.iloc[i]['手续费']
            fee_list.append(dict_item)
            # except:
            #     err_count = err_count + 1
            #     print('基金编码[%s' % (df.iloc[i]['基金代码']) + ']读取费用失败...')
            time.sleep(1)

        df_fee = pd.DataFrame(fee_list)
        df_fee.to_csv(filename, encoding='utf_8_sig', index=None)
        print('读取费率失败次数:%d' % err_count)
    else:
        df_fee = pd.read_csv(filename, dtype=object)

    return df_fee

def get_fund_base_info():
    """加载公募基金基础数据

    Returns:
        DataFrame: 公募基金基础数据
    """
    # 获得公募基金列表
    df = get_all_fund_outline()
    df = df[df['申购状态'] == '开放申购']

    # 加载费用
    df_fee = get_fund_fee_list(df)
    df_fee = df_fee[['基金代码', 'scale', 'm_fee', 'c_fee', 'sale_fee', 'sub_fee']].copy()

    # 合并基础信息和费用信息
    df = pd.merge(df, df_fee, on='基金代码')
    df.set_index(df['基金代码'])

    return df

# 计算基金rank
def get_fund_rank(fund_list, keywords, max_withdrawal, establish_year=3.0, start='2010-01-01', end='2200-01-01', min_scale=2.0, max_total_fee=2.0):
    """计算基金性能指标：年华收益率、最大回测、夏普比率、卡玛比率、手续费等信息

    Args:
        fund_list (list): 基金列表
        keywords (str): 筛选关键字
        max_withdrawal (float): 允许的最大回撤
        establish_year (float, optional): 最小基金建立年限. Defaults to 3.0.
        start (str, optional): 回测起始时间. Defaults to '1970-01-01'.
        end (str, optional): 回测结束时间. Defaults to '2200-01-01'.
        min_scale (float, optional): 最小基金规模. Defaults to 2.0.
        max_total_fee (float, optional): 最大手续费阈值. Defaults to 2.0.

    Returns:
        DateFrame: 基金性能指标
    """
    filename = f'{DIR_FUND_FILTER_RESULT_SORT_DATA}/fund_rank-{keywords}-{start}-{end}-{min_scale}-{establish_year}-{max_withdrawal}-{min_scale}-{max_total_fee}.xlsx'

    if not os.path.exists(DIR_FUND_FILTER_RESULT_SORT_DATA):
        os.makedirs(DIR_FUND_FILTER_RESULT_SORT_DATA)

    if os.path.exists(filename):
        dtype={
            'code':str,
            'years':float,
            'withdrawal':float,
            'annual_return':float,
            'total_return':float,
            'sharp':float,
            'calmar':float,
            'volatility':float,
            'name':str,
            'type':str,
            'scale':float,
            'm_fee':float,
            'c_fee':float,
            'sale_fee':float,
            'sub_fee':float,
            'total_fee':float
            }

        df_kpi = pd.read_excel(filename, dtype=dtype)
    else:
        fund_kpi_list = []

        # 根据关键字检索
        df_dist = query_fund_by_fundname_keyword(fund_list, keywords)

        df_dist = df_dist[df_dist['基金类型'].str.contains('场内') == False]
        for i in np.arange(0, df_dist.shape[0]):
            try:
                print('基金编码[%s'%(df_dist.iloc[i]['基金代码']) + ']正在读取...')

                # 爬取历史净值
                df_cumulative_net_value_trend = get_fund_his_by_id(df_dist.iloc[i]['基金代码'], DIR_CUMULATIVE_NET_VALUE_TREND, end)
                print('历史数据已加载...')
                if (keywords != '债') or (keywords == '债' and df_cumulative_net_value_trend['日增长率'].astype(float).max(skipna=True) <= 2.0):
                    # 计算基金KPI
                    dict_kpi = calc_fund_kpi(df_dist.iloc[i]['基金代码'], df_cumulative_net_value_trend, start, end)
                    dict_kpi['code'] = df_dist.iloc[i]['基金代码']
                    dict_kpi['name'] = df_dist.iloc[i]['基金简称']
                    dict_kpi['type'] = df_dist.iloc[i]['基金类型']
                    print('KPI计算已完成...')

                    # 爬取费用
                    dict_kpi['scale'] = df_dist.iloc[i]['scale']
                    dict_kpi['m_fee'] = df_dist.iloc[i]['m_fee']
                    dict_kpi['c_fee'] = df_dist.iloc[i]['c_fee']
                    dict_kpi['sale_fee'] = df_dist.iloc[i]['sale_fee']
                    dict_kpi['sub_fee'] = df_dist.iloc[i]['sub_fee']

                    # print(dict_kpi)
                    fund_kpi_list.append(dict_kpi)
                time.sleep(0.001)
            except Exception as e:  # 未知异常的捕获
                print(f"异常信息:{e}")  
                print('基金编码[%s'%(df_dist.iloc[i]['基金代码']) + ']读取失败')
            #     # time.sleep(1)

        # print(fund_kpi_list)
        df_kpi = pd.DataFrame(fund_kpi_list)
        # print(df_kpi)

        # 删除异常数据行
        # df_kpi.dropna(subset=['withdrawal'], inplace=True)
        try:
            df_kpi['total_fee'] = df_kpi['sub_fee'].astype(float) + df_kpi['m_fee'].astype(float) + df_kpi['c_fee'].astype(float) + df_kpi['sale_fee'].astype(float)
        except Exception as e:  # 未知异常的捕获
            print(f"异常信息:{e}")
            df_kpi['total_fee'] = 0
            print('[%s'%keywords + ']计算累计费用失败，跳过!')

        #  对数据筛选
        # 基金规模筛选
        df_kpi = df_kpi[df_kpi['scale'].astype(float) >= min_scale]
        # 成立年限筛选
        df_kpi = df_kpi[df_kpi['years'].astype(float) >= establish_year]
        # 最大回撤筛选
        df_kpi = df_kpi[df_kpi['withdrawal'].astype(float) <= max_withdrawal]
        # 基金费用
        df_kpi = df_kpi[df_kpi['total_fee'].astype(float) < max_total_fee]

        # 对数据排序, 'sharp', 'withdrawal', 'calmar', 'total_fee'
        df_kpi.sort_values(by=['sharp', 'withdrawal', 'calmar', 'total_fee'], ascending=[False, True, False, True], inplace=True)

        df_kpi.to_excel(f'{DIR_FUND_FILTER_RESULT_SORT_DATA}/fund_rank-{keywords}-{start}-{end}-{min_scale}-{establish_year}-{max_withdrawal}-{min_scale}-{max_total_fee}.xlsx')
    # print(df_kpi)
    print(f'{DIR_FUND_FILTER_RESULT_SORT_DATA}/fund_rank-{keywords}-{start}-{end}-{min_scale}-{establish_year}-{max_withdrawal}-{min_scale}-{max_total_fee}.xlsx 加载完毕！')
    return df_kpi

# 计算基金组合预测数据
def calc_fund_portfolio_net_value(fund_comb, start='2010-01-01', end='2200-01-01'):
    """计算基金组合KPI

    Args:
        fund_comb (list): 基金组合列表
        start (str, optional): 回测开始时间. Defaults to '2010-01-01'.
        end (str, optional): 回测结束时间. Defaults to '2200-01-01'.

    Returns:
        DataFrame: 基金组合增长率
    """
    df_comb = pd.DataFrame(columns=['净值日期', '复权净值', '复权净值临时', '日增长率'])

    for i in np.arange(0, fund_comb.shape[0]):
        # 爬取历史净值
        df = get_fund_his_by_id(fund_comb.iloc[i]['code'], DIR_CUMULATIVE_NET_VALUE_TREND, end)

        # df.dropna(axis=0, inplace=True)
        # df.fillna(method='pad',axis=0, inplace=True)

        # 过滤时间
        st = df['净值日期'].astype(str) >= start
        et = df['净值日期'].astype(str) <= end
        res = st == et
        df = df[res]

        if df_comb.empty:
            df_comb['净值日期'] = df['净值日期']
            df_comb.set_index('净值日期', inplace=True)

        df.set_index('净值日期', inplace=True)
        # print(df)

        # print(fund_comb.iloc[i]['share'])
        # if pd.isnull(df_comb.iloc[0]['复权净值']):
        if df_comb['复权净值'].isnull().all():
            df_comb['复权净值临时'] = 0.0
        else:
            df_comb.loc[:, '复权净值临时'] = df_comb.loc[:, '复权净值']

        # print(fund_comb.iloc[i][['code', 'share']], df_comb.loc[:, '复权净值'][0:5], df.loc[:, '复权净值'][0:5])
        df_comb.loc[:, '复权净值'] = df.loc[:, '复权净值'].astype(float) * fund_comb.iloc[i]['share']
        # print(type(df_comb.loc[:, '复权净值']), type(df_comb.loc[:, '复权净值临时']))
        df_comb.loc[:, '复权净值'] = df_comb.loc[:, '复权净值'].astype(float).add(df_comb.loc[:, '复权净值临时'])
        df_comb.fillna(method='pad', axis=0, inplace=True)

    # 计算日增长率
    df_comb['日增长率'] = (df_comb['复权净值'] - df_comb['复权净值'].shift(1))/df_comb['复权净值'].shift(1)

    # print(df_comb)
    return df_comb

def fund_portfolio_backtesting(fund_kinds_list, fund_share_cfg, start_date, end_date, fund_id_ref):
    """基金组合回测工具

    Args:
        fund_kinds_list (DateFrame list): 各种分类的大盘基金列表：沪深300、中证500等
        fund_share_cfg (list): 组合基金份额占比
        start_date (str): 回测开始日期
        end_date (str): 回测结束日期
        fund_id_ref (str): 沪深300参考基金
    """
    df_fund_portfolio = pd.DataFrame()
    for item in fund_kinds_list:
        df_fund_portfolio = df_fund_portfolio.append(item.iloc[0])

    # print(df_fund_portfolio)
    # print(fund_share_cfg)
    df_fund_portfolio.insert(loc=df_fund_portfolio.shape[1], column='share', value=fund_share_cfg)

    # print(df_fund_portfolio)
    # print(df_fund_portfolio.shape)

    dir_output = f"{DIR_OUTPUT}/{time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())}"
    if not os.path.exists(DIR_OUTPUT):
        os.makedirs(DIR_OUTPUT)

    if not os.path.exists(dir_output):
        os.makedirs(dir_output)

    # df_fund_portfolio.to_excel(f"{dir_output}/fund_portfolio_result.xlsx")
    df_fund_portfolio.to_csv(f"{dir_output}/fund_portfolio_result.csv", encoding='utf_8_sig', index=None)

    # 计算组合基金增长率
    df_fund_portfolio_kpi = calc_fund_portfolio_net_value(df_fund_portfolio, start_date, end_date)
    df_fund_portfolio_kpi.reset_index(inplace=True)
    x = df_fund_portfolio_kpi['净值日期']
    # y = df_fund_portfolio_kpi['复权净值']

    df_ref = get_fund_his_by_id(fund_id_ref, DIR_CUMULATIVE_NET_VALUE_TREND, end_date)
    con1=df_ref['净值日期'].astype(str) >= start_date
    con2=df_ref['净值日期'].astype(str) <= end_date
    df_ref2 = df_ref[con1&con2]

    # 计算基金组合性能指标
    calc_fund_kpi('fg0001', df_fund_portfolio_kpi, start_date, end_date)

    # 以起始时间作为累计净值的起点
    df_fund_portfolio_kpi['相对净值'] = (df_fund_portfolio_kpi['复权净值'].astype(float) - float(df_fund_portfolio_kpi.iloc[0]['复权净值'])) / float(df_fund_portfolio_kpi.iloc[0]['复权净值'])
    df_ref2['相对净值'] = (df_ref2['复权净值'].astype(float) - float(df_ref2.iloc[0]['复权净值'])) / float(df_ref2.iloc[0]['复权净值'])

    y = df_fund_portfolio_kpi['相对净值']
    y_ref = df_ref2['相对净值']

    df_fund_portfolio_kpi.to_csv(f"{dir_output}/自选组合基金回测数据.csv")
    df_ref2.to_csv(f"{dir_output}/沪深300基金参考.csv")

    # 绘制基金累计净值走势图
    draw_cumulative_net_value_trend(x, y, y_ref, dir_output)

    print("基金组合回测完毕！请打【开回测结果】目录查看报告和组合基金净值走势及与沪深300参考基金的收益对比！")

if __name__ == "__main__":
    pd.set_option('display.max_rows', 1000)
    pd.set_option('display.max_columns', 10)

    # 获得公募基金基础数据
    df_base = get_fund_base_info()

    # 大盘基金筛选
    df_kpi_csi300 = get_fund_rank(fund_list=df_base, keywords='沪深300', max_withdrawal=60.0, establish_year=5, start='2018-01-01', end='2022-10-31')
    df_kpi_csi500 = get_fund_rank(df_base, '中证500', 50.0, 5, '2018-01-01', '2022-10-31')
    df_kpi_gem = get_fund_rank(df_base, '创业板', 50.0, 5, '2018-01-01', '2022-10-31')
    df_kpi_gold = get_fund_rank(df_base, '黄金', 50.0, 5, '2018-01-01', '2022-10-31')
    df_kpi_bond = get_fund_rank(df_base, '债', 30.0, 5, '2018-01-01', '2022-10-31')
    df_kpi_sp500 = get_fund_rank(df_base, '标普500', 50.0, 5, '2018-01-01', '2022-10-31')
    df_kpi_nasda = get_fund_rank(df_base, '纳斯达克', 50.0, 5, '2018-01-01', '2022-10-31')

    # 定投基金组合回测
    fund_portfolio_backtesting(
        fund_kinds_list = [df_kpi_csi300, df_kpi_csi500, df_kpi_gem, df_kpi_gold, df_kpi_bond, df_kpi_sp500, df_kpi_nasda],
        fund_share_cfg = [0.05, 0.15, 0.10, 0.10, 0.20, 0.35, 0.05],
        start_date = '2018-01-01', end_date = '2022-10-31', fund_id_ref = '160706'
    )
  