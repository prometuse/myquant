# -*- coding:utf-8 -*-

import json

class Config:
    def __init__(self):
        self.api_key: str = None
        self.api_secret: str = None
        self.top_n_coins = 100
        self.pct_days = 3
        self.one_buy_ratio = 0.8
        self.sell_pct_rank_min = 20
        self.top_k_mm_buy = 3
        self.zhisun_pct = -100
        self.hours_cycle = 24  # 每N小时交易一次
        self.trade_time = 7  # 几点交易
        self.init_cash = 1_000_000
        self.proxy_host = ""  # proxy host
        self.proxy_port = 0  # proxy port
        self.buy_real = 0
        self.time_zone_diff = 0
        self.start_time = ""
        self.fetch_data_hours = 0
        self.zhiying_pct = -100
        self.btc_min_score = -100
        self.btc_max_score = 100

    def loads(self, config_file=None):
        """ Load config file.

        Args:
            config_file: config json file.
        """
        configures = {}
        if config_file:
            try:
                with open(config_file) as f:
                    data = f.read()
                    configures = json.loads(data)
            except Exception as e:
                print(e)
                exit(0)
            if not configures:
                print("config json file error!")
                exit(0)
        self._update(configures)

    def _update(self, update_fields):
        """
        更新update fields.
        :param update_fields:
        :return: None

        """

        for k, v in update_fields.items():
            setattr(self, k, v)

config = Config()
config.loads('../online_data/config/config.json')