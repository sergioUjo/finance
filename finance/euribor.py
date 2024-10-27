from finance import euribor_1m, euribor_3m, euribor_6m


async def curve(index):
    if index == "1M":
        return await euribor_1m.curve()
    elif index == "3M":
        return await euribor_3m.curve()
    elif index == "6M":
        return await euribor_6m.curve()