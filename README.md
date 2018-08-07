# Reget Bot
A Telegram bot to get book, movie, TV show, author, band, game recommendations based on your likes.

* Talk to [Reget Bot on Telegram](https://t.me/regetbot)  
* My [note](https://elma.pw/tr/notes/reget-bot/) about Reget Bot in Turkish

## English:

### Requirements
```
certifi==2018.1.18
future==0.16.0
python-telegram-bot==10.0.1
urllib3==1.22
```

### Preparation
Create a file called `secrets.py`. Then insert these lines to it;
```
_secret = {
    'tastedive_key': '',
    'bot_key': '',
    'admin_id': ,
}
```
Do not forget to add your Tastedive and bot keys to the defined fields. You can get a new Tastedive API key [here](https://tastedive.com/read/api).
*************************************
## Türkçe:

### Gereksinimler
```
certifi==2018.1.18
future==0.16.0
python-telegram-bot==10.0.1
urllib3==1.22
```

### Hazırlık
`secrets.py` isminde bir dosya oluşturun. Ardından, aşağıdaki satırları içerisine ekleyin;
```
_secret = {
    'tastedive_key': '',
    'bot_key': '',
    'admin_id': ,
}
```
Belirlenmiş alanlara Tastedive ve bot anahtarınızı eklemeyi unutmayın. Yeni bir Tastedive API anahtarını [buradan](https://tastedive.com/read/api) edinebilirsiniz.
