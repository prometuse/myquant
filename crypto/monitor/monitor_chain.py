#监控各区块链项目twitter情况
#pycharm
import tweepy
import time
import smtplib
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import parseaddr, formataddr
from email.mime.application import MIMEApplication

##########推特登录###########
consumer_key = '自行输入'
consumer_secret = '自行输入'
access_token = '自行输入'
access_token_secret = '自行输入'
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

time_now = time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())
file_name = "online_data/" + time_now + ".txt"
txt_file = open(file_name,'w')

for name in open("name.txt"):
user = api.get_user(name)
txt_file.write(str(user.followers_count))
txt_file.write('\n')
txt_file.close()

#################################
#############邮件发送##############
#################################
from_addr = '自行输入@qq.com'
mail_key = '自行输入'
to_addr = '自行输入@qq.com'
smtp_server = 'smtp.qq.com'

msg = MIMEMultipart()
msg.attach(MIMEText('当前各项目推特关注数', 'plain', 'utf-8'))
msg['From'] = from_addr
msg['To'] = to_addr
msg['Subject'] = Header('当前各项目twitter用户数追踪','utf-8').encode()

###################附件添加#########
email_file = MIMEApplication(open(file_name, 'rb').read())
email_file.add_header('Content-Disposition', 'attachment', filename=file_name)
msg.attach(email_file)

server = smtplib.SMTP(smtp_server, 25)
server.set_debuglevel(1)
server.login(from_addr,mail_key)
server.sendmail(from_addr,to_addr,msg.as_string())
server.quit()#退出邮箱服务器