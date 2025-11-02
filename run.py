from robota.robota import Robota
import robota.constant as const
from time import sleep

with Robota() as bot:
    bot.start_page()
    bot.choose_location("Київ")
    # bot.choose_worktype()
    bot.choose_salary(const.SALARY_ANY)
    bot.filter()
    bot.search_job("c++ developer")
    bot.parse()
    bot.save()