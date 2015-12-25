__author__ = 'YGK'
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import unicodedata
from re import findall

MY_USERNAME = "Enter-your-MAL-username"
MY_PASSWORD = "Enter-your-MAL-password"
MY_MAL_PAGE = "for example: http://myanimelist.net/animelist/Smith "
MY_CHROMEIUM_LOCATION = "Enter your local chromeium engine location. if you don't have one - download it"

class SiteChangeException(Exception):
    pass


def cast_array_unicode_to_string(array_unicode):
    """
    This function get a array with unicode values, and return it after converting it into string
    Using the "cast_unicode_to_string" function,
    :param array_unicode:
    :return: Array of strings
    """
    i = 0
    for unicode_value in array_unicode:
        array_unicode[i] = cast_unicode_to_string(unicode_value)
        i += 1
    return array_unicode


def cast_unicode_to_string(unicode_value):
    """
    Get a value in unicode, cast to string, and return the casted value
    :param unicode_value:
    :return:
    """
    return unicodedata.normalize('NFKD', unicode_value).encode('ascii', 'ignore')


def alert_anime(anime_instance, anime_updated_episode):
    print "!!! New episode of: \"%s\". Number %s" % (anime_instance.get_name(), anime_updated_episode)


def get_episode_number(anime_details):
    list_of_numbers = findall("[-+]?\d+[\.]?\d*", anime_details)
    last_number = list_of_numbers.pop()
    return last_number


class Anime:
    def __init__(self, name="unknown", current_episode_data=0):
        self.name = name
        if type(current_episode_data) != int:
            if current_episode_data.startswith("-"):
                self.current_episode = 0
            else:
                current_str_episode = findall("\d+/", current_episode_data)[0][:-1]
                self.current_episode = int(current_str_episode)
        else:
            print "Something has changed!"
            raise SiteChangeException

    def get_current_episode(self):
        return self.current_episode

    def set_current_episode(self, updated_episode):
        self.current_episode = updated_episode
        print "Anime \"%s\" updated episode to: %s" % (self.name, self.current_episode)

    def get_name(self):
        return self.name

    def set_name(self, updated_name):
        self.name = updated_name


class BrowserHandler:
    def __init__(self):
        self.browser_type = None
        self.driver = None
        self.is_login = None
        self.tracked_anime_list = []
        print "BrowserHandler Creation - Success"

    def open_firefox_browser(self):
        if self.browser_type == "Chrome":
            raise Exception("Can't open FireFox, When Chrome open")
        else:
            try:
                self.browser_type = "FireFox"
                print "FireFox Browser has been chosen"
                self.driver = webdriver.Firefox()
                print "Opened browser - Success"
            except Exception as e:
                print "Opened browser - Failure"
                print "Error message: %s" % e

    def open_chrome_browser(self):
        if self.browser_type == "FireFox":
            raise Exception("Can't open Chrome, When FireFox open")
        else:
            try:
                self.browser_type = "Chrome"
                print "Chrome Browser has been chosen"
                self.driver = webdriver.Chrome(executable_path=MY_CHROMEIUM_LOCATION)
                print "Opened browser - Success"
            except Exception as e:
                print "Opened browser - Failure"
                print "Error message: %s" % e

    def open_new_tab(self):
        try:
            body = self.driver.find_element_by_tag_name("body")
            body.send_keys(Keys.CONTROL + 't')
            print "Opened new tab"
            return True
        except Exception as e:
            print "Opened new tab has failed with exception: %s" % e
            return False

    def get_current_url(self):
        return self.driver.current_url

    def close_browser(self):
        driver_close_result = self.driver.close()
        if driver_close_result is None:
            self.browser_type = None
            print "Browser Close - Success"
        else:
            print "Browser Close - Failure"

    def refresh_browser(self):
        return self.driver.refresh()

    def get_mal_page(self):
        """
        Open the account page of your page on selected browser
        :return:
        """
        self.driver.get(MY_MAL_PAGE)

        
    def is_element_present(self, how, what):
        try:
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException:
            print "No Element with %s as %s has found" % (how, what)
            return False
        return True

    def check_mal_login(self):
        """
        Check if in account is logged-in to MAL, return True/False accordingly
        The current_driver should opened on a user page, doesn't matter whose
        :return:
        """
        try:
            self.driver.find_element_by_id("mal_cs_pic")
            print "User isn't logged-in"
            self.is_login = False
            return False
        except NoSuchElementException or Exception:
            print "User is logged-in"
            self.is_login = True
            return True

    def login_mal(self):
        self.driver.get("http://myanimelist.net/login.php")
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "loginUserName")))
            self.driver.find_element_by_id("loginUserName").send_keys(MY_USERNAME)
            self.driver.find_element_by_id("login-password").send_keys(MY_PASSWORD)
            self.driver.find_element_by_name("sublogin").click()
            print "Login - Success"
        except Exception, NoSuchElementException:
            print "Login - Failed"

    def get_anime_update_page(self):
        """
        Open the account page of your MAL on FireFox
        :return:
        """
        self.driver.get("http:/anime-update.com/")
        # Verification of the MAL page
        is_title_exist = self.is_element_present(By.TAG_NAME, "title")
        if is_title_exist is True:
            title_text = self.driver.execute_script('return document.getElementsByTagName("title")[0].text')
            if "Anime Update" in title_text:
                print "Opened Anime-Update site Page"
            else:
                print "Opened unrecognised page"
        else:
            print "The page's Title hasn't been found"

    def update_anime_list(self):
        """
        Read the 60 first animes on the site, and send message if one from the tracked list is up
        The Tracked_animes come from self.anime_list, Notice that the animes instance are from Anime class
        :return:
        """
        anime_instance_list = []
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "latestep_title")))
        try:
            anime_instance_list = self.driver.execute_script("""l = []
    all_new_animes = document.getElementsByClassName("latestep_wrapper")
    for (i=0; i<all_new_animes.length; i++){
    current_row = all_new_animes[i]
    current_title = current_row.getElementsByClassName("latestep_title")[0]
    if (typeof current_title != 'undefined'){
    title_text = current_title.textContent
    l[i] = title_text
    }
    }
    return l
    """)
        except Exception as e:
            print "Error on get anime_list, with: %s \nPossible a web change" % e
        finally:
            assert list == type(anime_instance_list)

        for anime_instance in anime_instance_list:
            if type(anime_instance) == 'NoneType' or anime_instance is None:
                break
            else:
                anime_details = unicodedata.normalize('NFKD', anime_instance).encode('ascii', 'ignore')
                tracked_anime = self.get_tracked(anime_details)
                if tracked_anime is not None:
                    # This Anime is tracked, and tracked_anime have it's instance
                    anime_updated_episode = get_episode_number(anime_details)
                    if tracked_anime.get_current_episode() < int(anime_updated_episode):
                        alert_anime(tracked_anime, anime_updated_episode)
                    else:
                        print "%s is already updated," % tracked_anime.get_name()
                else:
                    continue

    def add_anime_to_track(self, anime_name):
        self.tracked_anime_list.append(anime_name)
        print " \"%s\" has been added to your animes" % anime_name.get_name()

    def get_tracked(self, anime_details):
        """
        Return None if the anime_details doesn't appears in the tracked_anime_list
        In case it is - return the anime instance.
        :param anime_details: the anime_details that created from the anime_instance
        :return:
        """
        for anime in self.tracked_anime_list:
            if anime.get_name() in anime_details:
                return anime
        return None

    def get_current_tracked_animes(self):
        """
        Return a list of all the tracking animes at the moment.
        Known as the tracked_anime_list variable
        :return:
        """
        return self.tracked_anime_list

    def get_number_of_current_tracked_animes(self):
        """
        Return the number of animes that are tracking on at the moment.
        The length of the tracked_anime_list
        :return:
        """
        return len(self.tracked_anime_list)

    def get_watching_animes_from_MAL(self):
        """
        Note: This function isn't working on Chrome, the JS is enable to access the animes' episodes values.
        :return:
        """
        result_array = []
        animes_names = []
        animes_episodes = []
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "category_totals")))
        try:
            result_array = self.driver.execute_script("""mal_anime_names = []
mal_anime_episodes = []
animeSerialNum = 0
all_tables = document.getElementsByTagName("table");
for (var i=4; i < all_tables.length - 1; i++) // Run for the anime tables only
{
   table_spans = all_tables[i].getElementsByTagName("span");
   anime_name = table_spans[0].innerHTML
   mal_anime_names[animeSerialNum] = anime_name
   anime_episode = table_spans[2].outerText
   mal_anime_episodes[animeSerialNum] = anime_episode
   animeSerialNum++;
}
return [mal_anime_names, mal_anime_episodes]
    """)
        except Exception as e:
            print "Error on get anime_list, with: %s \nPossible a web change" % e
        finally:
            assert len(animes_episodes) == len(animes_names)

        animes_names = result_array[0]
        animes_names = cast_array_unicode_to_string(animes_names)
        animes_episodes = result_array[1]
        animes_episodes = cast_array_unicode_to_string(animes_episodes)

        # Until here we got 2 different arrays, with strings.
        # Now, we will create an Anime instance for each one.
        # And insert them into tracking.
        for index in xrange(len(animes_names)):
            self.add_anime_to_track(Anime(animes_names[index], animes_episodes[index]))

        assert self.get_number_of_current_tracked_animes() == len(animes_names)


if __name__ == "__main__":
    ffs = BrowserHandler()
    ffs.open_chrome_browser()

    ffs.get_mal_page_watching()
    ffs.check_mal_login()
    if ffs.is_login is False:
        ffs.login_mal()
    ffs.get_mal_page_watching()
    ffs.get_watching_animes_from_MAL()

    # ffs.open_new_tab()

    ffs.get_anime_update_page()
    ffs.update_anime_list()

    ffs.close_browser()
