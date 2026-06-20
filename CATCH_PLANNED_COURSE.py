import LOGIN
from bs4 import BeautifulSoup
import time
import re
from wvpn_login import jwxt_url

class PlannedCourse:
    def __init__(self, account):
        self.account = account
        # 最终选择的课程种类的url
        self.obj_url = ""
        # 所有课程种类的url
        self.urls = []
        # 所有开课信息
        self.course_list = []
        # 发送选课数据包的时候要用到
        self.obj_viewstate = ""

    def enter_planned_course(self):
        url = LOGIN.ZUCC.PlanCourageURL + "?xh=" + self.account.account_data["username"]
        header = LOGIN.ZUCC.InitHeader
        header["Referer"] = url
        
        # 获取选课页面
        response = self.account.session.get(url=url, headers=header)
        
        # 使用BeautifulSoup解析页面
        soup = BeautifulSoup(response.text, 'lxml')
        
        # 1. 提取专业名称
        zymc_input = soup.find('input', {'name': 'zymc'})
        if zymc_input:
            zymc_value = zymc_input.get('value', '')
            print("提取到专业名称:", zymc_value)
        else:
            print("未找到专业名称输入框，尝试使用页面已有数据...")
            # 可能已经在计划内选课页面，无需再次提交专业名称
            # 直接返回当前response用于爬取课程列表
            return response

        # 2. 构造POST请求参数
        post_data = {
            'zymc': zymc_value,         # 专业名称
            'Button5': '本专业选课',     # 触发按钮
            'xx': '',                    # 通常为年级信息（留空）
            'txtPjUrl': '',              # 可选课程路径（留空）
        }
        
        # 添加必要的ASP.NET隐藏字段
        hidden_fields = soup.find_all('input', type='hidden')
        for field in hidden_fields:
            name = field.get('name', '')
            value = field.get('value', '')
            if name:  # 只添加有名称的字段
                post_data[name] = value

        # 3. 提交选课请求
        submit_url = url  # POST目标地址（同当前页面）
        response = self.account.session.post(
            url=submit_url,
            headers=header,
            data=post_data
        )

        print("选课请求提交状态:", response.status_code)
        return response


    def catch_course(self):
        for info in self.course_list:
            info.show_course_info()
        n = input("输入编号(0退出)：")
        while True:
            if n == "0":
                return
            elif int(n) < 0 or int(n) > len(self.course_list):
                print("请输入正确的数字")
            else:
                break
        post_data = {"__EVENTTARGET": "Button1",
                     "__VIEWSTATEGENERATOR": "55DF6E88",
                     "xkkh": self.course_list[int(n) - 1].code,
                     "__VIEWSTATE": self.obj_viewstate,
                     "RadioButtonList1": 0}
        while True:
            header = LOGIN.ZUCC.InitHeader
            header["Referer"] = self.obj_url
            response = self.account.session.post(url=self.obj_url,headers=header, data=post_data)
            soup = BeautifulSoup(response.text, "lxml")
            try:
                script_tags = soup.find_all('script')
                for script in script_tags:
                    if script.string:
                        match = re.search(r"alert\('([^']+)'\);", script.string)
                        if match:
                            reply = match.group(1)
            except AttributeError as e:
                reply = "属性访问错误：" + str(e)
            except ValueError as e:
                reply = str(e)
            except Exception as e:
                reply = "其他未知错误：" + str(e)
            print(reply + "\t\t" + str(time.strftime('%m-%d-%H-%M-%S', time.localtime(time.time()))),flush=True)
            if reply == "选课成功！":
                return

    def choose_course_class(self, response):
        self.account.soup = BeautifulSoup(response.text, "lxml")
        links = self.account.soup.find_all(name="tr")
        for num, link in enumerate(links[1:-1]):
            tds = link.find_all("td")
            print("编号：" + str(num + 1) + "\t课程名称: " + tds[1].text)
            raw_url = "https://jwxt.buu.edu.cn/clsPage/xsxjs.aspx?" + "xkkh=" + \
                      tds[1].find("a").get("onclick").split("=")[1][0:-3] + "&xh=" + self.account.account_data["username"]
            url = jwxt_url(raw_url)
            # print(url)
            self.urls.append(url)

        n = input("输入编号：")
        url = self.urls[int(n) - 1]
        self.obj_url = url
        header = LOGIN.ZUCC.InitHeader
        header["Referer"] = jwxt_url("https://jwxt.buu.edu.cn/xs_main.aspx?xh=" + self.account.account_data['username'])
        item_response = self.account.session.get(url=url, headers=header)
        # print(BeautifulSoup(item_response.text, 'lxml'))
        item_soup = BeautifulSoup(item_response.text, "lxml")
        self.obj_viewstate = item_soup.find_all(name='input', id="__VIEWSTATE")[0]["value"]
        item_trs = item_soup.find_all(name="tr")
        for num, item_tr in enumerate(item_trs[1:]):
            try:
                tds = item_tr.find_all("td")
                code = tds[0].find('input').get('value')
                teacher = tds[2].text
                time = tds[3].text
                lessen = PlannedCourseInfo(num + 1, code, teacher, time)
                self.course_list.append(lessen)
            except BaseException:
                return
        return

    def run(self):
        response = self.enter_planned_course()
        if response is None:
            print("无法进入计划内选课页面")
            return
        self.choose_course_class(response)
        self.catch_course()


class PlannedCourseInfo:
    def __init__(self, num, code, teacher, time):
        self.num = str(num)
        self.code = str(code)
        self.teacher = str(teacher)
        self.time = str(time)

    def show_course_info(self):
        print("课程编号:" + self.num
              + "\t课程代码:" + self.code
              + "\t课程教师:" + self.teacher
              + "\t课程时间:" + self.time)

    def __contains__(self, item):
        if item in self:
            return True
        else:
            return False


if __name__ == '__main__':
    account = LOGIN.Account()
    account.login()
    planned = PlannedCourse(account)
    planned.run()
