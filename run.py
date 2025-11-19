from robota.robota import Robota, chooseWebdriver
from selenium import webdriver
import robota.constant as const
from time import sleep

# choose webdriver, default firefox
# chooseWebdriver(webdriver.Chrome)

with Robota() as bot:
    bot.start_page()
    bot.choose_location("Львів")
    # bot.choose_worktype()
    bot.choose_salary(const.SALARY_50K)
    # bot.filter()
    bot.search_job("c++ developer")
    bot.parse()
    bot.save("c++-developer-0.csv")