import _ensure_deps
_ensure_deps.ensure_dependencies()

import sys
import RW_ACCOUNT
import MENU
import CATCH_PUBLIC_COURSE as pub
import CATCH_PLANNED_COURSE as plan
import CATCH_OUTPLANNED_COURSE as outplan
import LOGIN
import os
import time
import OCR_CODE
import wvpn_login


def begin_catch_course():
    catch_course_dic = {
        "1": "培养方案选课",
        "2": "跨专业选课(已废弃)",
        "3": "通识教育选修（校选）课",
        "0": "返回主菜单",
    }
    catch_course_menu = MENU.MENU(catch_course_dic)
    catch_course_menu.print_list()
    while True:
        _key = input(">>>")
        if _key == "1":
            planned = plan.PlannedCourse(account)
            planned.run()
            catch_course_menu.print_list()
        elif _key == "2":
            outplanned = outplan.OutPlannedCourse(account)
            outplanned.run()
            catch_course_menu.print_list()
        elif _key == "3":
            public = pub.PublicCourse(account)
            public.run()
            catch_course_menu.print_list()
        elif _key == "0":
            return
        else:
            print("请输入正确的数字")


if __name__ == "__main__":

    # ====== 网络环境选择 ======
    print("\033[1;36m请选择当前网络环境：\033[0m")
    print("[1] 校内（直连教务系统）")
    print("[2] 校外（通过 WebVPN 访问）")
    while True:
        choice = input(">>> ").strip()
        if choice == "1":
            print("已选择：校内模式")
            break
        elif choice == "2":
            print("已选择：校外模式")
            print()
            wvpn_session = wvpn_login.authenticate()
            if wvpn_session is None:
                print("\033[1;31mWebVPN 登录失败，程序退出\033[0m")
                sys.exit()
            wvpn_login.configure_jwxt_urls()
            import LOGIN
            LOGIN._wvpn_session = wvpn_session
            break
        else:
            print("请输入 1 或 2")

    # ====== 原有逻辑 ======
    status = ""
    if os.path.exists("status.txt"):
        with open("status.txt", "r") as f:
            status = f.read()
    if status == "" or time.time() - int(status) > 600:
        print("OCR预热失效,OCR预热中")
        try:
            img_path = os.path.join(os.getcwd(), 'code.jpg')
            if not os.path.isfile(img_path):
                raise FileNotFoundError("warm-up image not available yet")
            with open(img_path, 'rb'):
                pass
        except OSError:
            print("OCR预热跳过（验证码图片暂不可用，登录后自动预热）")
        else:
            OCR_CODE.run(os.getcwd(), dir_now=os.getcwd())
            print("OCR预热完成")
            with open("status.txt", "w") as f:
                f.write(str(int(time.time())))
    print(
        "\033[1;36m       欢迎来到正方教务系统抢课助手\033[0m\n本程序主要自动登录+爬取课程信息+发送选课数据包进行抢课"
        "\n\033[1;31m第一次运行时记得先设置账号密码！之后运行就不需要设置了(存放在account.json中哦~)\033[0m"
    )
    init_dic = {"1": "设置账号密码", "2": "开始抢课", "0": "退出"}
    init_menu = MENU.MENU(init_dic)
    init_menu.print_list()
    while True:
        key = input(">>>")
        if key == "1":
            RW_ACCOUNT.set_account()
            init_menu.print_list()
        elif key == "2":
            account = LOGIN.Account()
            account.login()
            begin_catch_course()
            init_menu.print_list()
        elif key == "0":
            sys.exit()
        else:
            print("请输入正确的数字")
