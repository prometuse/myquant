
cd ../
rm online_mm.zip
#zip  -r online_mm.zip online/ utils/  gateway/ online_data/
zip  -r online_mm.zip online/ utils/ gateway/ trade/

scp online_mm.zip  ubuntu@152.32.144.246:/home/ubuntu/trade_mm_1