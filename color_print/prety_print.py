
class Colored(object):
    # 显示格式: \033[显示方式;前景色;背景色m
    # 只写一个字段表示前景色,背景色默认
    RED = '\033[31m'  # 红色
    GREEN = '\033[32m'  # 绿色
    YELLOW = '\033[33m'  # 黄色
    BLUE = '\033[34m'  # 蓝色
    FUCHSIA = '\033[35m'  # 紫红色
    CYAN = '\033[36m'  # 青蓝色
    WHITE = '\033[37m'  # 白色

    #: no color
    RESET = '\033[0m'  # 终端默认颜色

    def color_str(self, color, s):
        return '{}{}{}'.format(
            getattr(self, color),
            s,
            self.RESET
        )

    def red(self, s):
        return self.color_str('RED', s)

    def green(self, s):
        return self.color_str('GREEN', s)

    def yellow(self, s):
        return self.color_str('YELLOW', s)

    def blue(self, s):
        return self.color_str('BLUE', s)

    def fuchsia(self, s):
        return self.color_str('FUCHSIA', s)

    def cyan(self, s):
        return self.color_str('CYAN', s)

    def white(self, s):
        return self.color_str('WHITE', s)


def yellow_print(message):
    color = Colored()
    message = color.yellow(message)
    print(message)


def red_print(message):
    color = Colored()
    message = color.red(message)
    print(message)


def cyan_print(message):
    color = Colored()
    message = color.cyan(message)
    print(message)


def white_print(message):
    color = Colored()
    message = color.cyan(message)
    print(message)


def green_print(message):
    color = Colored()
    message = color.green(message)
    print(message)


def blue_print(message):
    color = Colored()
    message = color.blue(message)
    print(message)


def fuchsia_print(message):
    color = Colored()
    message = color.fuchsia(message)
    print(message)


if __name__ == '__main__':
    yellow_print('好嗨哟！')
    cyan_print('好嗨哟！')
    blue_print('好嗨哟！')
    red_print('好嗨哟！')
    white_print('好嗨哟！')
    fuchsia_print('好嗨哟！')
    green_print('好嗨哟！')
