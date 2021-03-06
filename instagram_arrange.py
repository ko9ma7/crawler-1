#-*- coding: utf-8 -*-

import re
import log
import random
import telegrambot
import filewriter
from time import sleep
from crawler2 import Crawler
from bs4 import BeautifulSoup
from datetime import datetime

class Instagram (Crawler):

    LOGIN_URL = 'https://www.instagram.com/accounts/login/?source=auth_switcher'
    TAG_URL = 'https://www.instagram.com/explore/tags/'
    UNFOLLOW_URL = 'https://www.instagram.com/kuhitlove/'
    FOLLOW_CNT = 0;
    FOLLOW_ACCEPT_CNT = 0;
    FOLLOWING_CANCEL_CNT = 0;
    LIKE_CNT = 0;
    REPLY_CNT = 0;
    FAIL_CNT = 0;
    CRITICAL_CNT = 0;
    FOLLOWER_CNT = 0;
    FOLLOWING_CNT = 0;
    REPLY = [];
    FOLLOWERS = [];
    FOLLOWINGS = [];
    TARGET_NAME = ''

    starttime = datetime.now()

    def start(self):
        try:
            self.login()

            # 팔로워 정리
            if self.follower() is True:
                # 팔로윙 정리
                self.following()

            self.end_report()

        except Exception as e:
            log.logger.error(e, exc_info=True)
            self.end_report()

    def end_report(self):
        duration = int((datetime.now() - self.starttime).total_seconds() / 60)
        log.logger.info('[durations %d min] Instagram process has completed. FOLLOWER_CNT (%d),FOLLOWING_CNT (%d),FOLLOW_CNT (%d), LIKE_CNT (%d), REPLY_CNT (%d), FOLLOW_ACCEPT_CNT (%d), FOLLOWING_CANCEL_CNT (%d), FAIL_CNT (%d)' % (duration, self.FOLLOWER_CNT, self.FOLLOWING_CNT, self.FOLLOW_CNT, self.LIKE_CNT, self.REPLY_CNT, self.FOLLOW_ACCEPT_CNT, self.FOLLOWING_CANCEL_CNT, self.FAIL_CNT))

        # 당분간 텔레그램으로 결과알림을 받자
        telegrambot.send_message('[durations %d min] Instagram process has completed. FOLLOWER_CNT (%d),FOLLOWING_CNT (%d),FOLLOW_CNT (%d), LIKE_CNT (%d), REPLY_CNT (%d), FOLLOW_ACCEPT_CNT (%d), FOLLOWING_CANCEL_CNT (%d), FAIL_CNT (%d)' % (duration, self.FOLLOWER_CNT, self.FOLLOWING_CNT, self.FOLLOW_CNT, self.LIKE_CNT, self.REPLY_CNT, self.FOLLOW_ACCEPT_CNT, self.FOLLOWING_CANCEL_CNT, self.FAIL_CNT), 'dev')

        self.FOLLOW_CNT = 0;
        self.LIKE_CNT = 0;
        self.REPLY_CNT = 0;
        self.FAIL_CNT = 0;
        self.REPLY = [];

        self.destroy()
        exit()

    def login(self):
        try:
            if self.connect(site_url=self.LOGIN_URL, is_proxy=False,
                            default_driver='selenium',
                            is_chrome=True) is False:
                raise Exception('site connect fail')

            # 계정정보 가져오기
            account_data = filewriter.get_log_file('instagram_account')

            if account_data:
                if self.selenium_extract_by_xpath(tag={'tag': 'input', 'attr': 'name', 'name': 'username'}) is False:
                    raise Exception('selenium_extract_by_xpath fail.')

                # 아이디 입력
                if self.selenium_input_text_by_xpath(text=account_data[0], tag={'tag': 'input', 'attr': 'name', 'name': 'username'}) is False:
                    raise Exception('selenium_input_text_by_xpath fail. username')

                # 비번 입력
                if self.selenium_input_text_by_xpath(text=account_data[1], tag={'tag': 'input', 'attr': 'name', 'name': 'password'}) is False:
                    raise Exception('selenium_input_text_by_xpath fail. password')

                # 로그인하기 선택
                if self.selenium_click_by_xpath(tag={'tag': 'button', 'attr': 'type', 'name': 'submit'}) is False:
                    raise Exception('selenium_click_by_xpath fail. submit')

                sleep(3)

                log.logger.info('login success')

                return True
        except Exception as e:
            log.logger.error(e, exc_info=True)
            self.CRITICAL_CNT = self.CRITICAL_CNT + 1
            self.end_report()

        return False

    # 팔로워 정리
    def follower(self):
        try:
            if self.connect(site_url=self.UNFOLLOW_URL, is_proxy=False, default_driver='selenium', is_chrome=True) is False:
                raise Exception('site connect fail')

            if self.selenium_click_by_xpath(xpath='//*[@id="react-root"]/section/main/div/header/section/ul/li[2]/a') is False:
                raise Exception('selenium_extract_by_xpath fail.')

            if self.selenium_extract_by_xpath(xpath='/html/body/div[3]/div/div[2]/ul/div/li[1]') is False:
                raise Exception('selenium_extract_by_xpath fail.')

            # 스크롤 내려서 모두 불러오기
            if self.scroll_bottom(selectorParent='document.getElementsByClassName("isgrP")[0]', selectorDom='document.getElementsByClassName("_6xe7A")[0]', limit_page=9999) is False:
                raise Exception('scroll bottom fail.')

            followers = self.driver.find_element_by_xpath('/html/body/div[3]/div/div[2]/ul')
            if followers:
                soup_list_follewers = BeautifulSoup(followers.get_attribute('innerHTML'), 'html.parser')
                for follower in soup_list_follewers.find_all('li'):
                    try:
                        if follower:
                            soup_follower_link = follower.find('a', class_='FPmhX')
                            if soup_follower_link:
                                follower_id = soup_follower_link.getText().strip()
                                # print('%s' % (follower_id))

                                # 팔로워 목록에 추가
                                if follower_id not in self.FOLLOWERS:
                                    self.FOLLOWERS.append(follower_id)
                    except Exception:
                        continue

            # print(self.FOLLOWERS)
            log.logger.info('followers list. (%s)' % (','.join(self.FOLLOWERS)))

            self.selenium_click_by_xpath(xpath='/html/body/div[3]/div/div[1]/div/div[2]/button')

            return True

        except Exception as e:
            log.logger.error(e, exc_info=True)

        return False

    # 팔로윙 정리
    def following(self):
        try:
            # 현재 팔로워, 팔로윙 숫자
            follower = self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/header/section/ul/li[2]/a/span')
            if follower:
                soup_follewer = BeautifulSoup(follower.get_attribute('innerHTML'), 'html.parser')
                self.FOLLOWER_CNT = soup_follewer.getText().strip()
                self.FOLLOWER_CNT = int(self.FOLLOWER_CNT)

            following = self.driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/header/section/ul/li[3]/a/span')
            if following:
                soup_following = BeautifulSoup(following.get_attribute('innerHTML'), 'html.parser')
                self.FOLLOWING_CNT = soup_following.getText().strip()
                self.FOLLOWING_CNT = int(self.FOLLOWING_CNT)

            gap_follow = self.FOLLOWING_CNT - self.FOLLOWER_CNT - 150;

            # 최신 200명에 대해서는 취소 X
            limit_cancel_following = self.FOLLOWING_CNT - 200
            # limit_cancel_following = 20

            log.logger.info('FOLLOWER_CNT (%d)' % (self.FOLLOWER_CNT))
            log.logger.info('FOLLOWING_CNT (%d)' % (self.FOLLOWING_CNT))
            log.logger.info('gap_follow (%d)' % (gap_follow))
            log.logger.info('limit_cancel_following (%d)' % (limit_cancel_following))

            if limit_cancel_following < 0:
                return True

            if self.selenium_click_by_xpath(
                    xpath='//*[@id="react-root"]/section/main/div/header/section/ul/li[3]/a') is False:
                raise Exception('selenium_extract_by_xpath fail.')

            if self.selenium_extract_by_xpath(xpath='/html/body/div[3]/div/div[2]/ul/div/li[1]') is False:
                raise Exception('selenium_extract_by_xpath fail.')

            # 스크롤 내려서 모두 불러오기
            if self.scroll_bottom(selectorParent='document.getElementsByClassName("isgrP")[0]', selectorDom='document.getElementsByClassName("_6xe7A")[0]', limit_page=9999) is False:
                raise Exception('scroll bottom fail.')

            # 아래부터 팔로우 취소
            list = self.driver.find_elements_by_xpath('/html/body/div[3]/div/div[2]/ul/div/li')

            for li in reversed(list):
                try:
                    # 15분동안 30회 취소 후 종료
                    # if self.FOLLOWING_CANCEL_CNT >= self.FOLLOW_CNT + 1:
                    # if self.FOLLOWING_CANCEL_CNT >= self.FOLLOW_CNT + self.FOLLOW_ACCEPT_CNT:
                    if limit_cancel_following < 0:
                        break

                    limit_cancel_following = limit_cancel_following - 1

                    elem_following = li.find_element_by_xpath('.//a[contains(@class,"FPmhX")]')
                    if elem_following:
                        id_following = elem_following.text
                        log.logger.info('check following id. (%s)' % (id_following))
                        if id_following not in self.FOLLOWERS:
                            cancel_following = li.find_element_by_xpath('.//button[contains(@class,"_8A5w5")]')
                            if cancel_following:
                                cancel_following.click()
                                self.selenium_click_by_xpath(xpath='/html/body/div[4]/div/div/div[3]/button[1]')
                                self.FOLLOWING_CANCEL_CNT = self.FOLLOWING_CANCEL_CNT + 1
                                log.logger.info('following canceled. (%s)' % (id_following))
                                gap_follow = gap_follow - 1
                                sleep(25)
                        else:
                            log.logger.info('following exist. (%s)' % (id_following))
                except Exception as e:
                    log.logger.error(e, exc_info=True)
                    gap_follow = gap_follow - 1
                    limit_cancel_following = limit_cancel_following - 1
                    continue

            return True

        except Exception as e:
            log.logger.error(e, exc_info=True)

        return False

    # 스크롤 가장 아래로
    def scroll_bottom(self, selectorParent=None, selectorDom=None, limit_page=0):
        try:
            if selectorParent is None or selectorDom is None:
                return False

            is_success = True
            same_count = 0
            limit = 1

            # Get scroll height
            last_height = self.driver.execute_script("return "+selectorDom+".scrollHeight")

            while True:
                try:
                    if limit_page > 0:
                        if limit > limit_page:
                            break;

                    if same_count > 5:
                        break

                    # Scroll down to bottom
                    self.driver.execute_script(selectorParent+".scrollTo(0, "+selectorDom+".scrollHeight);")

                    # Wait to load page
                    sleep(2)

                    # Calculate new scroll height and compare with last scroll height
                    new_height = self.driver.execute_script("return "+selectorDom+".scrollHeight")
                    limit = limit + 1
                    log.logger.info('scroll bottom %d steps.' % (limit))

                    if new_height == last_height:
                        log.logger.info('More list fail')
                        same_count = same_count + 1
                    else:
                        log.logger.info('More list sucess')
                        same_count = 0

                    last_height = new_height
                except Exception as e:
                    is_success = False
                    log.logger.error(e, exc_info=True)
                    break

            return is_success

            # log.logger.info('last_height: %d' % (last_height))
        except Exception as e:
            log.logger.error(e, exc_info=True)
            return False

if __name__ == "__main__":
    cgv = Instagram()
    cgv.utf_8_reload()
    cgv.start()
