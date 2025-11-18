from robota.robota import Robota, chooseWebdriver
from selenium import webdriver
import robota.constant as const
from time import sleep

# choose webdriver, default firefox
# chooseWebdriver(webdriver.Chrome)

with Robota() as bot:
    bot.start_page()
    bot.choose_location("Дніпро")
    # bot.choose_worktype()
    bot.choose_salary(const.SALARY_50K)
    # bot.filter()
    bot.search_job("python developer")
    bot.parse()
    bot.save("python-developer-0.csv")