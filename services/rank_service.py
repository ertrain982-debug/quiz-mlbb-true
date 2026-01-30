def get_rank_data(score: int):
    if score < 100:
        return "Воин", "🟤", "images/ranks/warrior.png"
    elif score < 200:
        return "Элита", "⚪️", "images/ranks/elite.png"
    elif score < 350:
        return "Мастер", "🟡", "images/ranks/master.png"
    elif score < 600:
        return "Грандмастер", "🟠", "images/ranks/grandmaster.png"
    elif score < 1000:
        return "Эпик", "🟢", "images/ranks/epic.png"
    elif score < 1500:
        return "Легенда", "🟣", "images/ranks/legend.png"
    else:
        return "Мифик", "🔴", "images/ranks/mythic.png"