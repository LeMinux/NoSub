import unittest
import sys
import os
import json
import sqlite3
from requests.models import Response

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import nosub

from unittest.mock import patch
from unittest.mock import call

class ValidationMethods(unittest.TestCase):
    empty = ""
    spaces = "          "
    white_space = "\t\n\v \b"

    #This tests if a file exists and can read it
    #of course the user could pass in something like /etc/passwd
    #as that does have read set for everyone
    #links can be a bit tricky as superficially they have all permissions,
    #so to get the actual permissions these do need to be resolved
    def testValidFile(self):
       self.assertTrue(nosub.checkFile("./cur_dir_test.txt"))

    def testImplicitCurDirFile(self):
        self.assertTrue(nosub.checkFile("cur_dir_test.txt"))

    def testValidLink(self):
        self.assertTrue(nosub.checkFile("./TestFiles/link_to_good_file.txt"))

    def testLinkChaining(self):
        self.assertTrue(nosub.checkFile("./TestFiles/link_to_link"))

    def testNotRealFile(self):
        self.assertFalse(nosub.checkFile("somerandomfilewow.random"))

    #sudoers has -r--r-----
    def testNoReadPerms(self):
        self.assertFalse(nosub.checkFile("/etc/sudoers"))

    def testLinkToNoReadPerms(self):
        self.assertFalse(nosub.checkFile("./TestFiles/link_to_root"))

    def testBrokenLink(self):
        self.assertFalse(nosub.checkFile("./TestFiles/broken_link.txt"))

    def testDirectoryAsFile(self):
        self.assertFalse(nosub.checkFile("./TestFiles/"))

    def testNoFileName(self):
        self.assertFalse(nosub.checkFile(self.empty))

    def testFileAsSpaces(self):
        self.assertFalse(nosub.checkFile(self.spaces))

    def testFileAsMoreWhiteSpace(self):
        self.assertFalse(nosub.checkFile(self.white_space))

    #test convertToMinutes
    valid_number = "8"
    def test8ToSecond(self):
        self.assertEqual(nosub.convertToMinutes(self.valid_number, "second"), 8/60)

    def test8ToSeconds(self):
        self.assertEqual(nosub.convertToMinutes(self.valid_number, "seconds"), 8/60)

    def test8ToMinute(self):
        self.assertEqual(nosub.convertToMinutes(self.valid_number, "minute"), 8)

    def test8ToMinutes(self):
        self.assertEqual(nosub.convertToMinutes(self.valid_number, "minutes"), 8)

    def test8ToHour(self):
        self.assertEqual(nosub.convertToMinutes(self.valid_number, "hour"), 480)

    def test8ToHours(self):
        self.assertEqual(nosub.convertToMinutes(self.valid_number, "hours"), 480)

    def test8ToDay(self):
        self.assertEqual(nosub.convertToMinutes(self.valid_number, "day"), 11520)

    def test8ToDays(self):
        self.assertEqual(nosub.convertToMinutes(self.valid_number, "days"), 11520)

    def test8ToWeek(self):
        self.assertEqual(nosub.convertToMinutes(self.valid_number, "week"), 80640)

    def test8ToWeeks(self):
        self.assertEqual(nosub.convertToMinutes(self.valid_number, "weeks"), 80640)

    def test8ToMonth(self):
        self.assertEqual(nosub.convertToMinutes(self.valid_number, "month"), 350640)

    def test8ToMonths(self):
        self.assertEqual(nosub.convertToMinutes(self.valid_number, "months"), 350640)

    def test8ToYear(self):
        self.assertEqual(nosub.convertToMinutes(self.valid_number, "year"), 4207680)

    def test8ToYears(self):
        self.assertEqual(nosub.convertToMinutes(self.valid_number, "years"), 4207680)

    def testBigNumberToYears(self):
        valid_big_number = "5000"
        self.assertEqual(nosub.convertToMinutes(valid_big_number, "years"), 2629800000)

    def testWeridWayOfSayingOne(self):
        valid_weird_one = "00000001"
        self.assertEqual(nosub.convertToMinutes(valid_weird_one, "minutes"), 1)

    def testPassingInZero(self):
        invalid_zero = "0"
        self.assertEqual(nosub.convertToMinutes(invalid_zero, "minutes"), -1)

    def testPassingNegativeOne(self):
        invalid_negative = "-1"
        self.assertEqual(nosub.convertToMinutes(invalid_negative, "minutes"), -1)

    def testPassingALargeNegativeToOverflow(self):
        invalid_big_negative = "-999999999999999999999"
        self.assertEqual(nosub.convertToMinutes(invalid_big_negative, "minutes"), -1)

    def testPassingInANumberWithLetter(self):
        invalid_number = "27m"
        self.assertEqual(nosub.convertToMinutes(invalid_number, "minutes"), -1)

    def testPassingIncorrectUnit(self):
        invalid_unit = "yers"
        self.assertEqual(nosub.convertToMinutes(self.valid_number, invalid_unit), -1)

    def testSwappedParameters(self):
        self.assertEqual(nosub.convertToMinutes("hours", self.valid_number), -1)

    def testEmptyNumber(self):
        self.assertEqual(nosub.convertToMinutes("", "weeks"), -1)

    def testEmptyUnit(self):
        self.assertEqual(nosub.convertToMinutes(self.valid_number, ""), -1)

    #validate handle strings
    def testValidateAValidHandle(self):
        valid_handle = "TestGuy3"
        self.assertEqual(nosub.validateHandle(valid_handle), True)

    def testValidateAnInvalidHandle(self):
        invalid_handle = "IAmAReallyLongHandleThatCannotOccur"
        self.assertEqual(nosub.validateHandle(invalid_handle), False)

    def testPassingMaliciousHandle(self):
        invalid_handle = "0 OR 1=1;--"
        self.assertEqual(nosub.validateHandle(invalid_handle), False)

    def testPassingMaliciousHandle2(self):
        invalid_handle = "0 OR 1-true"
        self.assertEqual(nosub.validateHandle(invalid_handle), False)

    def testValidateAnEmptyHandle(self):
        self.assertEqual(nosub.validateHandle(self.empty), False)

    def testValidateHandleThatIsWhiteSpace(self):
        self.assertEqual(nosub.validateHandle(self.spaces), False)

    def testValidateHandleThatIsMoreWhiteSpace(self):
        self.assertEqual(nosub.validateHandle(self.white_space), False)

    #validate video id strings
    def testPassingValidVideoId(self):
        valid_id = "AB7pBrudFbg"
        self.assertEqual(nosub.validateVideoId(valid_id), True)

    def testPassingVideoIdWithMultipleDashes(self):
        valid_id = "--FS3QW4QuE"
        self.assertEqual(nosub.validateVideoId(valid_id), True)

    def testPassingVideoIdWithMultipleUnderscores(self):
        valid_id = "OoETj__HfVg"
        self.assertEqual(nosub.validateVideoId(valid_id), True)

    def testPassingVideoIdThatIsTooShort(self):
        invalid_id = "AB7prudFbg"
        self.assertEqual(nosub.validateVideoId(invalid_id), False)

    def testPassingVideoIdThatIsTooLong(self):
        invalid_id = "AB7prudgeFbg"
        self.assertEqual(nosub.validateVideoId(invalid_id), False)

    def ValidateInvalidVideoId(self):
        invalid_id = "8^![l]|e783"
        self.assertEqual(nosub.validateVideoId(invalid_id), False)

    def testPassingEmtpyVideoId(self):
        self.assertEqual(nosub.validateVideoId(self.empty), False)

    def testValidateVideoIdThatIsWhiteSpace(self):
        self.assertEqual(nosub.validateVideoId(self.spaces), False)

    def testValidateVideoIdThatIsMoreWhiteSpace(self):
        self.assertEqual(nosub.validateVideoId(self.white_space), False)

    #validate release id strings
    def testValidateValidReleaseId(self):
        valid_id = "OLAK5uy_mqUpJnm37KuCU0D5kF4SdvqTkK0WGIdWg"
        self.assertEqual(nosub.validateReleaseId(valid_id), True)

    def testValidateReleaseIdWithDash(self):
        valid_id = "OLAK5uy_kvdrBzs4x1W-bcTd0XhVdWTxks30L3GhI"
        self.assertEqual(nosub.validateReleaseId(valid_id), True)

    def testValidateReleaseIdWithManyUnderscores(self):
        valid_id = "OLAK5uy_l8val_6FdXgV0jPfDGWiXG5Dq-YELTp5E"
        self.assertEqual(nosub.validateReleaseId(valid_id), True)

    def testValidateValidReleaseIdThatIsTooShort(self):
        invalid_id = "mqUpJnm37KuCU0D5kF4SdvqTkK0WGIdWg"
        self.assertEqual(nosub.validateReleaseId(invalid_id), False)

    def testValidateValidReleaseIdThatIsTooLong(self):
        invalid_id = "OLAK5uy_mqUpJnm37KuCU0D5kF4SdvqTkK0WGIdWgdawg"
        self.assertEqual(nosub.validateReleaseId(invalid_id), False)

    def testValidateValidReleaseIdWithInvalidCharacters(self):
        invalid_id = "OLAK5uy_m!U'Jnm37KuCU0D;kF4SdvqT K0WGIdWw"
        self.assertEqual(nosub.validateReleaseId(invalid_id), False)

    def testValidateEmptyReleaseId(self):
        self.assertEqual(nosub.validateReleaseId(self.empty), False)

    def testValidateReleaseIdThatIsWhiteSpace(self):
        self.assertEqual(nosub.validateReleaseId(self.spaces), False)

    def testValidateReleaseIdThatIsMoreWhiteSpace(self):
        self.assertEqual(nosub.validateReleaseId(self.white_space), False)


class TestExecutionFlags(unittest.TestCase):
    def setUp(self):
        self.patcher_norm_exec = patch("nosub.normalExec")
        self.patcher_real_exec = patch("nosub.releaseExec")
        self.patcher_init = patch("nosub.init")

        self.mock_norm = self.patcher_norm_exec.start()
        self.mock_real = self.patcher_real_exec.start()
        self.mock_init = self.patcher_init.start()

        self.mock_norm.return_value = None
        self.mock_real.return_value = None
        self.mock_init.return_value = 0

    def tearDown(self):
        self.patcher_norm_exec.stop()
        self.patcher_real_exec.stop()

    def testPassing8ToDashN(self):
        sys.argv = ["nosub.py", "-f", "./cur_dir_test.txt", "-n", "8"]
        nosub.main()
        self.mock_norm.assert_called_once()
        self.mock_real.assert_not_called()

    def testPassing8ToLongFormNumber(self):
        sys.argv = ["nosub.py", "-f", "./cur_dir_test.txt", "--number", "8"]
        nosub.main()
        self.mock_norm.assert_called_once()
        self.mock_real.assert_not_called()


    def testPassing1ToDashN(self):
        sys.argv = ["nosub.py", "-f", "cur_dir_test.txt", "-n", "1"]
        nosub.main()
        self.mock_norm.assert_called_once()
        self.mock_real.assert_not_called()

    def testPassing0ToDashN(self):
        sys.argv = ["nosub.py", "-f", "cur_dir_test.txt", "-n", "0"]
        with self.assertRaises(SystemExit):
            nosub.main()

    def testPassingNegative1ToDashN(self):
        sys.argv = ["nosub.py", "-f", "cur_dir_test.txt", "-n", "-1"]
        with self.assertRaises(SystemExit):
            nosub.main()

    def testPassingLargeNegativeToDashN(self):
        sys.argv = ["nosub.py", "-f", "cur_dir_test.txt", "-n", "-999999999999999999999"]
        with self.assertRaises(SystemExit):
            nosub.main()

class TestJsonExtraction(unittest.TestCase):
    videos = "videos"
    releases = "releases"
    empty = ""

    def setUp(self):
        self.patcher_request = patch("requests.get")

        self.mock_req = self.patcher_request.start()

        self.mock_req.return_value = None
        self.mock_req.side_effect = Exception("Early Exit")

    def tearDown(self):
        self.patcher_request.stop()

    def testPassingVideoAndValidHandle(self):
        valid_handle = "GTARadioSoundtracks"
        with self.assertRaises(Exception):
            nosub.obtainElements(self.videos, valid_handle)

    def testPassingReleasesAndValidHandle(self):
        valid_handle = "GTARadioSoundtracks"
        with self.assertRaises(Exception):
            nosub.obtainElements(self.releases, valid_handle)

    def testPassingCompleteURLAsHandle(self):
        invalid_handle = "https://www.youtube.com/watch?v=Fjp0wu3lEHk&list=PLLvWV__Bn2_PwR92FfrxjsZCAM7zyxzze&index=2"
        self.assertEqual(nosub.obtainElements(self.releases, invalid_handle), None)

    def testPassingCompleteYoutuberPage(self):
        invalid_handle = "https://www.youtube.com/@WillTennyson"
        self.assertEqual(nosub.obtainElements(self.releases, invalid_handle), None)

    def testPassingHandleWithTabAtEnding(self):
        invalid_handle = "GrayStillPlays/video" #shouldn't give the /vidoe at the end
        self.assertEqual(nosub.obtainElements(self.videos, invalid_handle), None)

    def testPassingThreeSlashes(self):
        invalid_handle = "///"
        self.assertEqual(nosub.obtainElements(self.videos, invalid_handle), None)

    def testHandleWithNewLine(self):
        invalid_handle = "GTARadioSoundtracks\n"
        self.assertEqual(nosub.obtainElements(self.videos, invalid_handle), None)

    def testPassingEmptyHandle(self):
        self.assertEqual(nosub.obtainElements(self.videos, self.empty), None)

    def testPassingMaliciousURL(self):
        invalid_handle = "https://www.y0utvbe.com/@superhacker"
        self.assertEqual(nosub.obtainElements(self.videos, invalid_handle), None)

    def testPassingInvalidHandle(self):
        invalid_handle = "thedoubtfultechn!cian"
        self.assertEqual(nosub.obtainElements(self.videos, invalid_handle), None)

    #Tests actual extraction of data
    #The previous test about arguments exists since the arguments passed here
    #will not directly relate to what JSON it would get of actual execution
    #since the JSON will be mocked for consistency.
    #The JSONs are extracted from real channels though
class JsonExtraction(unittest.TestCase):
    videos_tab = "videos"
    releases_tab = "releases"
    test_handle = "SomeTestHandle"

    @classmethod
    def setUpClass(cls):
        #raw data
        file1 = open("./TestData/htmls/one_video.html", "rb")
        file2 = open("./TestData/htmls/one_video_no_semicolon.html", "rb")
        file3 = open("./TestData/htmls/loaded_from_videos.html", "rb")
        file4 = open("./TestData/htmls/loaded_from_releases.html", "rb")
        file5 = open("./TestData/htmls/no_content.html", "rb")
        file6 = open("./TestData/htmls/loaded_from_home.html", "rb")
        file7 = open("./TestData/htmls/not_real.html", "rb")

        #conceptually there is no difference in videos vs releases in how it's extracted
        #but if the internals were to change this is here to catch it
        #no_content and loaded_home are also slightly different as no_content
        #will not have the title tag, but loading from the home page can still
        #have the title with none of the content
        cls.one_video = file1.read()
        cls.no_semi = file2.read()
        cls.loaded_videos = file3.read()
        cls.loaded_releases = file4.read()
        cls.no_content = file5.read()
        cls.loaded_home =  file6.read()
        cls.not_real = file7.read()

        file1.close()
        file2.close()
        file3.close()
        file4.close()
        file5.close()
        file6.close()
        file7.close()

        #expected data to get
        exp_file1 = open("./TestData/ContentsJsons/one_video.json", "rb")
        exp_file2 = open("./TestData/ContentsJsons/loaded_from_releases.json", "rb")
        exp_file3 = open("./TestData/ContentsJsons/loaded_from_videos.json", "rb")

        cls.exp_one_video = json.load(exp_file1)
        cls.exp_loaded_releases = json.load(exp_file2) #loaded from /releases tab
        cls.exp_loaded_videos = json.load(exp_file3)   #loaded from /videos tab

        exp_file1.close()
        exp_file2.close()
        exp_file3.close()

    def setUp(self):
        self.patcher_request = patch("requests.get")
        self.mock_req = self.patcher_request.start()

    def tearDown(self):
        self.patcher_request.stop()

    def testExtractingAPageWithOneVideo(self):
        self.mock_req.return_value.status_code = 200
        self.mock_req.return_value.content = self.one_video
        self.assertEqual((nosub.obtainElements(self.videos_tab, self.test_handle)), self.exp_one_video["contents"])

    def testExtractingWhereThereIsNoSemiColon(self):
        self.mock_req.return_value.status_code = 200
        self.mock_req.return_value.content = self.no_semi
        self.assertEqual(nosub.obtainElements(self.videos_tab, self.test_handle), self.exp_one_video["contents"])

    def testExtractingVideos(self):
        self.mock_req.return_value.status_code = 200
        self.mock_req.return_value.content = self.loaded_videos
        self.assertEqual(nosub.obtainElements(self.videos_tab, self.test_handle), self.exp_loaded_videos["contents"])

    def testExtractingReleases(self):
        self.mock_req.return_value.status_code = 200
        self.mock_req.return_value.content = self.loaded_releases
        self.assertEqual(nosub.obtainElements(self.releases_tab, self.test_handle), self.exp_loaded_releases["contents"])

    def testExtractingVideosOnAReleaseTab(self):
        self.mock_req.return_value.status_code = 200
        self.mock_req.return_value.content = self.loaded_releases
        self.assertEqual(nosub.obtainElements(self.videos_tab, self.test_handle), None)

    def testExtractingReleasesOnAVideoTab(self):
        self.mock_req.return_value.status_code = 200
        self.mock_req.return_value.content = self.loaded_videos
        self.assertEqual(nosub.obtainElements(self.releases_tab, self.test_handle), None)

    def testExtractingVideosOnNoContent(self):
        self.mock_req.return_value.status_code = 200
        self.mock_req.return_value.content = self.no_content
        self.assertEqual(nosub.obtainElements(self.videos_tab, self.test_handle), None)

    def testExtractingReleasesOnNoContent(self):
        self.mock_req.return_value.status_code = 200
        self.mock_req.return_value.content = self.no_content
        self.assertEqual(nosub.obtainElements(self.releases_tab, self.test_handle), None)

    def testExtractingVideosFromHomeTab(self):
        self.mock_req.return_value.content = self.loaded_home
        self.assertEqual(nosub.obtainElements(self.videos_tab, self.test_handle), None)

    def testExtractingReleasesFromHomeTab(self):
        self.mock_req.return_value.content = self.loaded_home
        self.assertEqual(nosub.obtainElements(self.releases_tab, self.test_handle), None)

    def testUnavailableYoutuber(self):
        self.mock_req.return_value.status_code = 404
        self.mock_req.return_value.content = self.not_real
        self.assertEqual(nosub.obtainElements(self.releases_tab, self.test_handle), None)

#With the usage of parameterized queries SQL injections won't be able to occur.
#I'm still testing them though because SQL injections are garbage data
#that will mess up behavior as the database will be trying to look for
#"OR 1=1 instead of an id like jC_z1vL1OCI
class TestDataBase(unittest.TestCase):
    videos_table = "KnownVideos"
    releases_table = "KnownReleases"
    invalid_table = "Videos"
    id_field = "known_id"

    #create db needed for testing
    @classmethod
    def setUpClass(cls):
        cls.testing_connection = sqlite3.connect("Testing.db")

        #seed database with consistent data
        cursor = cls.testing_connection.cursor()

        create_videos = """
        CREATE TABLE IF NOT EXISTS KnownVideos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handle varchar(30) UNIQUE NOT NULL,
            known_id varchar(11) UNIQUE NOT NULL
        );
        """
        create_releases = """
        CREATE TABLE IF NOT EXISTS KnownReleases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handle varchar(30) UNIQUE NOT NULL,
            known_id varchar(41) UNIQUE NOT NULL
        );
        """

        add_videos = """
            INSERT INTO KnownVideos (handle, known_id) VALUES
            ('smartereveryday', 'JVROsxtjoCw'),
            ('veritasium', 'P_fHJIYENdI')
        """

        add_releases = """
            INSERT INTO KnownReleases (handle, known_id) VALUES
            ('NeonNox', 'OLAK5uy_kH4jLV7RYNpdfuuVT529OLzvFdKPLyDcA'),
            ('BuddhaTrixie', 'OLAK5uy_mIg7sAsw6VFdUtKzOxlOWfJ9NU4ueknQ0')
        """

        #delete any existing data before adding new data
        delete_videos = "DELETE FROM KnownVideos"
        delete_releases = "DELETE FROM KnownReleases"

        cursor.execute(create_videos)
        cursor.execute(create_releases)

        cursor.execute(delete_videos)
        cursor.execute(delete_releases)

        cursor.execute(add_videos)
        cursor.execute(add_releases)
        cls.testing_connection.commit()


    @classmethod
    def tearDownClass(cls):
        cls.testing_connection.close()

        #deletion is done during begining of execution that was the database
        #can be inspected before starting new tests

    def setUp(self):
        self.patcher_db_conn = patch("nosub.connectToDB", side_effect = self.mocked_connection)
        self.mock_connection = self.patcher_db_conn.start()
        self.cursor = self.testing_connection.cursor()

    def tearDown(self):
        self.patcher_db_conn.stop()

    def mocked_connection(self):
        if not self.testing_connection:
            self.testing_connection = sqlite3.connect("Testing.db")

        return self.testing_connection

    #Don't need to include all the tests that exist for validating handles and ids
    #Do need to test some as testing how the method reacts to invalid input is still important
    #even if it is assumed the validation methods will catch it
    def testAddingNewHandleAndVideo(self):
        valid_handle = "TestGuy1"
        valid_video_id = "AB7pBrudFbg"
        self.assertEqual(nosub.addId(valid_handle, valid_video_id, self.videos_table), 0)
        result = self.cursor.execute(f"SELECT COUNT(id) FROM {self.videos_table} WHERE {self.id_field} = '{valid_video_id}' AND handle = '{valid_handle}';")
        self.assertEqual(result.fetchone()[0], 1)

    def testAddingNewHandleAndReleaseId(self):
        valid_handle = "TestGuy1"
        valid_release_id = "OLAK5uy_mqUpJnm37KuCU0D5kF4SdvqTkK0WGIdWg"
        self.assertEqual(nosub.addId(valid_handle, valid_release_id, self.releases_table), 0)
        result = self.cursor.execute(f"SELECT COUNT(id) FROM {self.releases_table} WHERE {self.id_field} = '{valid_release_id}' AND handle = '{valid_handle}';")
        self.assertEqual(result.fetchone()[0], 1)

    def testAddingAHandleThatIsInvalid(self):
        invalid_handle = "IAmAReallyLongHandleThatCannotOccur"
        valid_release_id = "OLAK5uy_mqUpJnm37KuCU0D5kF4SdvqTkK0WGIdWg"
        self.assertEqual(nosub.addId(invalid_handle, valid_release_id, self.releases_table), -1)

    def testAddingVideoIdThatHasInvalidCharacters(self):
        valid_handle = "TestGuy6"
        invalid_video_id3 = "8^![l]|e783"
        self.assertEqual(nosub.addId(valid_handle, invalid_video_id3, self.videos_table), -1)

    def testAddingReleaseIdThatHasInvalidCharacters(self):
        valid_handle = "TestGuy6"
        invalid_release_id2 = "OLAK5uy_m!U'Jnm37KuCU0D;kF4SdvqT K0WGIdWw"
        self.assertEqual(nosub.addId(valid_handle, invalid_release_id2, self.releases_table), -1)

    def testAddingEmptyHandle(self):
        empty = ""
        valid_video_id = "AB7pBrudFbg"
        self.assertEqual(nosub.addId(empty, valid_video_id, self.videos_table), -1)

    def testAddingEmptyVideoId(self):
        valid_handle = "TestGuy7"
        empty = ""
        self.assertEqual(nosub.addId(valid_handle, empty, self.videos_table), -1)

    def testAddingEmptyReleaseId(self):
        valid_handle = "TestGuy7"
        empty = ""
        self.assertEqual(nosub.addId(valid_handle, empty, self.releases_table), -1)

    #|----------|
    #| Updating |
    #|----------|

    def testUpdatingWithVideoId(self):
        video_handle = "smartereveryday"
        update_video = "lylCYkgC63Q"
        self.assertEqual(nosub.addId(video_handle, update_video, self.videos_table), 0)
        result = self.cursor.execute(f"SELECT COUNT(id) FROM {self.videos_table} WHERE {self.id_field} = '{update_video}' AND handle = '{video_handle}';")
        self.assertEqual(result.fetchone()[0], 1)

    def testUpdatingWithReleaseId(self):
        release_handle = "NeonNox"
        update_release = "OLAK5uy_mQYefdFy2Kk8UPkdiJA6gnOvu3wfFATHU"
        self.assertEqual(nosub.addId(release_handle, update_release, self.releases_table), 0)
        result = self.cursor.execute(f"SELECT COUNT(id) FROM {self.releases_table} WHERE {self.id_field} = '{update_release}' AND handle = '{release_handle}';")
        self.assertEqual(result.fetchone()[0], 1)

    def testUpdatingWithAnInvalidVideoId(self):
        video_handle = "smartereveryday"
        invalid_update_video = "8^![l]|e783"
        self.assertEqual(nosub.addId(video_handle, invalid_update_video, self.videos_table), -1)

    def testUpdatingWithAnInvalidReleaseId(self):
        release_handle = "NeonNox"
        invalid_update_release = "OLAK5uy_m!U'Jnm37KuCU0D;kF4SdvqT K0WGIdWw"
        self.assertEqual(nosub.addId(release_handle, invalid_update_release, self.releases_table), -1)

    def testUpdatingUsingAnEmptyHandle(self):
        empty = ""
        update_video = "lylCYkgC63Q"
        self.assertEqual(nosub.addId(empty, update_video, self.videos_table), -1)

    def testUpdatingUpdatingUsingAnEmptyVideoId(self):
        video_handle = "smartereveryday"
        empty = ""
        self.assertEqual(nosub.addId(video_handle, empty, self.videos_table), -1)

    def testUpdatingUpdatingUsingAnEmptyReleaseId(self):
        release_handle = "NeonNox"
        empty = ""
        self.assertEqual(nosub.addId(release_handle, empty, self.releases_table), -1)

    #|---------|
    #| Finding |
    #|---------|

    def testFindingValidHandleAndVideoId(self):
        video_handle = "veritasium"
        find_video_id = "P_fHJIYENdI"
        self.assertEqual(nosub.findId(video_handle, find_video_id, self.videos_table), True)

    def testFindingValidHandleAndReleaseId(self):
        release_handle = "BuddhaTrixie"
        find_release_id = "OLAK5uy_mIg7sAsw6VFdUtKzOxlOWfJ9NU4ueknQ0"
        self.assertEqual(nosub.findId(release_handle, find_release_id, self.releases_table), True)

    def testFindingInvalidHandleButValidVideoId(self):
        handle_not_in_db = "HeHeHeHa"
        find_video_id = "P_fHJIYENdI"
        self.assertEqual(nosub.findId(handle_not_in_db, find_video_id, self.videos_table), False)

    def testFindingInvalidHandleButValidReleaseId(self):
        handle_not_in_db = "HeHeHeHa"
        find_release_id = "OLAK5uy_mIg7sAsw6VFdUtKzOxlOWfJ9NU4ueknQ0"
        self.assertEqual(nosub.findId(handle_not_in_db, find_release_id, self.releases_table), False)

    def testFindingValidHandleButInvalidVideoId(self):
        video_handle = "veritasium"
        video_id_not_in_db = "7md_gd3HuMQ"
        self.assertEqual(nosub.findId(video_handle, video_id_not_in_db, self.videos_table), False)

    def testFindingValidHandleButInvalidReleaseId(self):
        release_handle = "BuddhaTrixie"
        release_id_not_in_db = "OLAK5uy_ncH3yFRhelTJAfdpWp4CigIDPGnjihZvs"
        self.assertEqual(nosub.findId(release_handle, release_id_not_in_db, self.videos_table), False)

    def testFindingEmptyHandleWithValidId(self):
        video_handle = ""
        video_id_in_db = "P_fHJIYENdI"
        self.assertEqual(nosub.findId(video_handle, video_id_in_db, self.videos_table), False)

    def testFindingEmptyId(self):
        video_handle = "veritasium"
        video_id_not_in_db = ""
        self.assertEqual(nosub.findId(video_handle, video_id_not_in_db, self.videos_table), False)

    #find handle
    def testFindingValidVideoHandle(self):
        video_handle = "veritasium"
        self.assertEqual(nosub.findHandle(video_handle, self.videos_table), True)

    def testFindingValidReleaseHandle(self):
        release_handle = "BuddhaTrixie"
        self.assertEqual(nosub.findHandle(release_handle, self.releases_table), True)

    def testFindingHandleNotInDB(self):
        handle_not_in_db = "HeHeHeHa"
        self.assertEqual(nosub.findHandle(handle_not_in_db, self.videos_table), False)

    def testFindingEmptyVideoHandle(self):
        empty_handle = ""
        self.assertEqual(nosub.findHandle(empty_handle, self.videos_table), False)

    def testFindingEmptyReleaseHandle(self):
        empty_handle = ""
        self.assertEqual(nosub.findHandle(empty_handle, self.releases_table), False)

    #|-------------------|
    #| Duplicate testing |
    #|-------------------|

    def testInsertingDuplicateVideoId(self):
        non_dup_handle = "Dummy"
        valid_video_id = "AB7pBrudFbg"
        with self.assertRaises(SystemExit):
            nosub.addId(non_dup_handle, valid_video_id, self.videos_table)

    def testInsertingDuplicateReleaseId(self):
        non_dup_handle = "Dummy"
        valid_release_id = "OLAK5uy_mqUpJnm37KuCU0D5kF4SdvqTkK0WGIdWg"
        with self.assertRaises(SystemExit):
            nosub.addId(non_dup_handle, valid_release_id, self.releases_table)

    #a duplicate handle would just result in an update
    """
    def testInsertingDuplicateHandle(self):
        valid_handle = "smartereveryday"
        non_dup_id = "JVROsxtjoCw"
        with self.assertRaises(SystemExit):
            nosub.addId(valid_handle, non_dup_id, self.videos_table)
    """

    #|-----------------------|
    #| SQL injection testing |
    #|-----------------------|

    #the sql injections are testing the INSERT portion
    #SELECT COUNT(*) FROM KnownVideos WHERE handle = ?;
    #INSERT INTO KnownVideos (handle, known_id) VALUES (<handle>, <id>)

    def testAddingSQLInjection(self):
        sql_injection =  "50); DELETE FROM KnownReleases;--        " #try to delete all releases
        valid_handle = "TestGuy8"
        self.assertEqual( nosub.addId(valid_handle, sql_injection, self.releases_table), -1)

    def testAddingSQLInjection2(self):
        sql_injection2 = "OLAK5uy_le); DELETE FROM KnownReleases;--" #try to delete all releases
        valid_handle = "TestGuy9"
        self.assertEqual( nosub.addId(valid_handle, sql_injection2, self.releases_table), -1)

    def testAddingSQLInjection3(self):
        sql_injection3 = "0);--      " #try to insert an id of zero to videos
        valid_handle = "TestGuy10"
        self.assertEqual(nosub.addId(valid_handle, sql_injection3, self.videos_table), -1)

    #these sql injections are testing the updating portion
    #SELECT COUNT(*) FROM KnownVideos WHERE handle = ?;
    #UPDATE KnownVideos SET known_id = <id> WHERE handle = <handle>;

    def testUpdatingSQLInjection(self):
        video_handle = "smartereveryday"
        sql_injection =  "\"OR 1=1;-- "
        self.assertEqual( nosub.addId(video_handle, sql_injection, self.videos_table), -1)

    def testUpdatingSQLInjection2(self):
        video_handle = "smartereveryday"
        sql_injection2 = "'OR 1=1;-- "
        self.assertEqual( nosub.addId(video_handle, sql_injection2, self.videos_table), -1)

    def testUpdatingSQLInjection3(self):
        video_handle = "smartereveryday"
        sql_injection3 = "\"\"OR 1=1;--"
        self.assertEqual(nosub.addId(video_handle, sql_injection3, self.videos_table), -1)

    def testUpdatingSQLInjection4(self):
        video_handle = "smartereveryday"
        sql_injection4 = "2 OR 1=1;--"
        self.assertEqual(nosub.addId(video_handle, sql_injection4, self.videos_table), -1)

    def testUpdatingSQLInjection5(self):
        release_handle = "NeonNox"
        sql_injection5 = "injected' WHERE 'blue' = 'blue';--      "
        self.assertEqual(nosub.addId(release_handle, sql_injection5, self.releases_table), -1)

    #these sql injections are for the finding portion
    #SELECT COUNT(id) FROM KnownVideos WHERE known_id = <id> AND handle = <handle>;

    def testFindingSQLInjection(self):
        video_handle = "veritasium"
        sql_injection =  "\"OR 1=1;-- "
        self.assertEqual( nosub.findId(video_handle, sql_injection, self.videos_table), False)

    def testFindingSQLInjection2(self):
        video_handle = "veritasium"
        sql_injection2 = "'OR 1=1;-- "
        self.assertEqual( nosub.findId(video_handle, sql_injection2, self.videos_table), False)

    def testFindingSQLInjection3(self):
        video_handle = "veritasium"
        sql_injection3 = "\"\"OR 1=1;--"
        self.assertEqual(nosub.findId(video_handle, sql_injection3, self.videos_table), False)

    def testFindingSQLInjection4(self):
        video_handle = "veritasium"
        sql_injection4 = "2 OR 1=1;--"
        self.assertEqual(nosub.findId(video_handle, sql_injection4, self.videos_table), False)

    def testFindingSQLInjection5(self):
        release_handle = "BuddhaTrixie"
        sql_injection5 = "injected' WHERE 'blue' = 'blue';--      "
        self.assertEqual(nosub.findId(release_handle, sql_injection5, self.releases_table), False)

    def testFindingSQLInjection6(self):
        release_handle = "BuddhaTrixie"
        sql_injection6 = "LIKE '%HJ%'"
        self.assertEqual(nosub.findId(release_handle, sql_injection6, self.videos_table), False)

#Separate method so that a different testing DB can be used
class ClearDataBase(unittest.TestCase):
    #create db needed for testing
    @classmethod
    def setUpClass(cls):
        cls.testing_connection = sqlite3.connect("DeleteTesting.db")

        #seed database with consistent data
        cursor = cls.testing_connection.cursor()

        create_videos = """
        CREATE TABLE IF NOT EXISTS KnownVideos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handle varchar(30) UNIQUE NOT NULL,
            known_id varchar(11) UNIQUE NOT NULL
        );
        """
        create_releases = """
        CREATE TABLE IF NOT EXISTS KnownReleases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handle varchar(30) UNIQUE NOT NULL,
            known_id varchar(41) UNIQUE NOT NULL
        );
        """

        add_videos = """
            INSERT INTO KnownVideos (handle, known_id) VALUES
            ('smartereveryday', 'JVROsxtjoCw'),
            ('veritasium', 'P_fHJIYENdI')
        """

        add_releases = """
            INSERT INTO KnownReleases (handle, known_id) VALUES
            ('NeonNox', 'OLAK5uy_kH4jLV7RYNpdfuuVT529OLzvFdKPLyDcA'),
            ('BuddhaTrixie', 'OLAK5uy_mIg7sAsw6VFdUtKzOxlOWfJ9NU4ueknQ0')
        """

        #delete any existing data before adding new data
        delete_videos = "DELETE FROM KnownVideos"
        delete_releases = "DELETE FROM KnownReleases"

        cursor.execute(create_videos)
        cursor.execute(create_releases)

        cursor.execute(delete_videos)
        cursor.execute(delete_releases)

        cursor.execute(add_videos)
        cursor.execute(add_releases)
        cls.testing_connection.commit()


    @classmethod
    def tearDownClass(cls):
        cls.testing_connection.close()

    def setUp(self):
        self.patcher_db_conn = patch("nosub.connectToDB", side_effect = self.mocked_connection)
        self.mock_connection = self.patcher_db_conn.start()

    def tearDown(self):
        self.patcher_db_conn.stop()

    def mocked_connection(self):
        if not self.testing_connection:
            self.testing_connection = sqlite3.connect("DeleteTesting.db")

        return self.testing_connection

    def testClearData(self):
        cursor = self.testing_connection.cursor()
        option = "--clear-knowns"
        with self.assertRaises(SystemExit) as ex:
            sys.argv = ["nosub.py", "-f", "cur_dir_test.txt", option]
            nosub.main()
            video_result = cursor.execute(f"SELECT COUNT(id) FROM {self.videos_table};")
            release_result = cursor.execute(f"SELECT COUNT(id) FROM {self.releases_table};")
            self.assertEqual(video_result.fetchone()[0], 0)
            self.assertEqual(release_result.fetchone()[0], 0)

        self.assertEqual(ex.exception.code, 0)


#Tests the actual execution of the program
#Some things are mocked so that it can be done offline and with consistency

#the test file used contains 6 entries
#5 of which result in a 200 response with data
#1 is a response that results in a 404 and no content

#1 uploads multiple videos daily so gives a streak of new videos
#1 is that of a channel that took a long break in uploads
#1 is about monthly uploads
#1 is about weekly uploads
#1 channel uploads whenever
class NormalExecutionTesting(unittest.TestCase):
    videos_table = "KnownVideos"
    videos_tab = "videos"
    id_field = "known_id"

    @classmethod
    def setUpClass(cls):
        cls.testing_connection = sqlite3.connect("NormalExecutionTesting.db")
        cursor = cls.testing_connection.cursor()

        create_videos = """
        CREATE TABLE IF NOT EXISTS KnownVideos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handle varchar(30) UNIQUE NOT NULL,
            known_id varchar(11) UNIQUE NOT NULL
        );
        """
        #delete any existing data before adding new data
        delete_videos = "DELETE FROM KnownVideos"

        cursor.execute(create_videos)
        cursor.execute(delete_videos)

        cls.testing_connection.commit()

        file1 = open("./TestData/ExecutionHtmls/Long_Break_An0nymooose.html", "rb")
        file2 = open("./TestData/ExecutionHtmls/Many_Daily_Uploads_Romanian_Tvee.html", "rb")
        file3 = open("./TestData/ExecutionHtmls/7_Hour_Upload_Technology_Connections.html", "rb")
        file4 = open("./TestData/ExecutionHtmls/5_Day_Upload_The_Doubtful_Technician.html", "rb")
        file5 = open("./TestData/ExecutionHtmls/Changed_Their_Handle.html", "rb")
        file6 = open("./TestData/ExecutionHtmls/Weekly_Uploads_Will_Tennyson.html", "rb")

        cls.anonymooose = file1.read()
        cls.romanian_tvee = file2.read()
        cls.technology_connections = file3.read()
        cls.doubtful_technician = file4.read()
        cls.change_handle = file5.read()
        cls.will_tennyson = file6.read()

        file1.close()
        file2.close()
        file3.close()
        file4.close()
        file5.close()
        file6.close()

    @classmethod
    def tearDownClass(cls):
        cls.testing_connection.close()

    def setUp(self):
        self.patcher_request = patch("requests.get", side_effect = self.mockObtainHtmls)
        self.patcher_db_conn = patch("nosub.connectToDB", side_effect = self.mocked_connection)
        self.patcher_mock_browser = patch("webbrowser.open_new_tab")

        self.patcher_request.start()
        self.patcher_db_conn.start()
        self.mock_browser = self.patcher_mock_browser.start()

        self.mock_browser.return_value = None

    def tearDown(self):
        self.patcher_request.stop()
        self.patcher_db_conn.stop()
        self.patcher_mock_browser.stop()

    def mockObtainHtmls(self, *args, **kwargs):
        response = Response()
        if args[0] == "https://www.youtube.com/@an0nymooose/videos":
            response.status_code = 200
            response._content = self.anonymooose

        elif args[0] == "https://www.youtube.com/@TechnologyConnections/videos":
            response.status_code = 200
            response._content = self.technology_connections

        elif args[0] == "https://www.youtube.com/@RomanianTvee/videos":
            response.status_code = 200
            response._content = self.romanian_tvee

        elif args[0] == "https://www.youtube.com/@thedoubtfultechnician/videos":
            response.status_code = 200
            response._content = self.doubtful_technician

        elif args[0] == "https://www.youtube.com/@thedoubtfultechnician8067/videos":
            response.status_code = 404
            response._content = self.change_handle

        elif args[0] == "https://www.youtube.com/@WillTennyson/videos":
            response.status_code = 200
            response._content = self.will_tennyson
        else:
            raise Exception(f"Mocked html elements did not get expected args. Got {args}")

        return response

    def mocked_connection(self):
        if not self.testing_connection:
            self.testing_connection = sqlite3.connect("ExecutionTesting.db")

        return self.testing_connection

    def clearDB(self):
        cursor = self.testing_connection.cursor()
        cursor.execute("DELETE FROM KnownVideos")
        self.testing_connection.commit()

    #despite any execution the most recent video should be in the db
    def verifyPostDB(self):
        cursor = self.testing_connection.cursor()
        rtv_handle = "RomanianTvee"
        mooose_handle = "an0nymooose"
        tech_connection_handle = "TechnologyConnections"
        doubt_tech_handle = "thedoubtfultechnician"
        will_tenny_handle = "WillTennyson"
        new_rtv_id = "pqYu8-JjXNQ"
        new_will_tenny_id = "T3d-c1TAQQg"
        new_tech_connection_id = "QEJpZjg8GuA"
        new_mooose_id = "RzNkY1_Nk3o"
        new_doubt_tech_id = "fq--H6KvqUg"

        with self.subTest(msg = f"Testing handle {rtv_handle} is set to have id {new_rtv_id}"):
            result = cursor.execute(f"SELECT COUNT(id) FROM {self.videos_table} WHERE {self.id_field} = '{new_rtv_id}' AND handle = '{rtv_handle}';")
            self.assertEqual(result.fetchone()[0], 1)

        with self.subTest(msg = f"Testing handle {will_tenny_handle} is set to have id {new_will_tenny_id}"):
            result = cursor.execute(f"SELECT COUNT(id) FROM {self.videos_table} WHERE {self.id_field} = '{new_will_tenny_id}' AND handle = '{will_tenny_handle}';")
            self.assertEqual(result.fetchone()[0], 1)

        with self.subTest(msg = f"Testing handle {tech_connection_handle} is set to have id {new_tech_connection_id}"):
            result = cursor.execute(f"SELECT COUNT(id) FROM {self.videos_table} WHERE {self.id_field} = '{new_tech_connection_id}' AND handle = '{tech_connection_handle}';")
            self.assertEqual(result.fetchone()[0], 1)

        with self.subTest(msg = f"Testing handle {mooose_handle} is set to have id {new_mooose_id}"):
            result = cursor.execute(f"SELECT COUNT(id) FROM {self.videos_table} WHERE {self.id_field} = '{new_mooose_id}' AND handle = '{mooose_handle}';")
            self.assertEqual(result.fetchone()[0], 1)

        with self.subTest(msg = f"Testing handle {doubt_tech_handle} is set to have id {new_doubt_tech_id}"):
            result = cursor.execute(f"SELECT COUNT(id) FROM {self.videos_table} WHERE {self.id_field} = '{new_doubt_tech_id}' AND handle = '{doubt_tech_handle}';")
            self.assertEqual(result.fetchone()[0], 1)

    #with no stopping point and time frame given this should just load the first videos seen
    def testNormalFromFreshStartWithDefaultSettings(self):
        self.clearDB()
        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/videos.txt"]
        nosub.main()
        self.assertEqual(self.mock_browser.call_count, 5)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=pqYu8-JjXNQ"), #rtv
            call("https://www.youtube.com/watch?v=RzNkY1_Nk3o"), #mooose
            call("https://www.youtube.com/watch?v=QEJpZjg8GuA"), #tech connect
            call("https://www.youtube.com/watch?v=fq--H6KvqUg"), #doubt tech
            call("https://www.youtube.com/watch?v=T3d-c1TAQQg")  #will tenny
        ]
        #order doesn't really matter if every thing is loaded
        #also would be annoying having to order it
        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()

    #Just checking if the verbose prints out
    #this doesn't really care if the program runs correctly but that verbosity is printed
    def testNormalVerbose(self):
        self.clearDB()
        cursor = self.testing_connection.cursor()
        add_videos = """
            INSERT INTO KnownVideos (handle, known_id) VALUES
            ('thedoubtfultechnician', 'fq--H6KvqUg')
        """
        cursor.execute(add_videos)
        self.testing_connection.commit()

        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/verbose_video.txt", "-v"]
        #redirect output to a file
        with open("verbose_test_videos.txt", "w") as verbose_test:
            original_out = sys.stdout
            sys.stdout = verbose_test
            nosub.main()
            sys.stdout = original_out


        #read redirect file
        contents = ""
        with open("verbose_test_videos.txt", "r") as verbose_test:
            contents = verbose_test.read()
            self.assertTrue("checking handle TechnologyConnections" in contents)
            self.assertTrue("checking handle thedoubtfultechnician" in contents)
            self.assertTrue("Loading URL https://www.youtube.com/watch?v=QEJpZjg8GuA" in contents)
            self.assertTrue("Youtube channel thedoubtfultechnician has not uploaded in 5 days" in contents)

    def testNormalFromFreshStartWithMultipleFilesDefaultSettings(self):
        self.clearDB()
        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/videos_split_1.txt", "./TestFiles/ExecutionTesting/videos_split_2.txt"]
        nosub.main()
        self.assertEqual(self.mock_browser.call_count, 5)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=RzNkY1_Nk3o"),
            call("https://www.youtube.com/watch?v=pqYu8-JjXNQ"),
            call("https://www.youtube.com/watch?v=QEJpZjg8GuA"),
            call("https://www.youtube.com/watch?v=fq--H6KvqUg"),
            call("https://www.youtube.com/watch?v=T3d-c1TAQQg")
        ]
        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()

    #test a streak of videos from RomanianTvee
    #id already known from TechnologyConnections
    #handle not known yet from thedoubtfultechnician
    #normal case with WillTennyson and anonymooose
    #   anonymooose having the case of two years break
    def testNormalWithSomeDataInDatabaseDefaultSettings(self):
        self.clearDB()
        cursor = self.testing_connection.cursor()
        add_videos = """
            INSERT INTO KnownVideos (handle, known_id) VALUES
            ('RomanianTvee', '3W0yMU06_pY'),
            ('an0nymooose', 'G84YqORpjHk'),
            ('WillTennyson', 'Y3oXlvHhdsk'),
            ('TechnologyConnections', 'QEJpZjg8GuA')
        """
        cursor.execute(add_videos)
        self.testing_connection.commit()

        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/videos.txt"]
        nosub.main()
        #3 from RomanianTvee
        #2 from WillTennyson
        #1 from an0nymooose
        #0 from TechnologyConnections
        #1 from thedoubtfultechnician
        self.assertEqual(self.mock_browser.call_count, 7)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=pqYu8-JjXNQ"), #RTV first id seen
            call("https://www.youtube.com/watch?v=W2DdVFeq1WM"), #RTV
            call("https://www.youtube.com/watch?v=dyFCyOWq8PY"), #RTV
            call("https://www.youtube.com/watch?v=T3d-c1TAQQg"), #Tennyson first id seen
            call("https://www.youtube.com/watch?v=lFzccuoS3ag"), #Tennyson
            call("https://www.youtube.com/watch?v=RzNkY1_Nk3o"), #an0ny
            call("https://www.youtube.com/watch?v=fq--H6KvqUg")  #doubt tech
        ]
        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()

    #only 30 videos are given at a time so the program will not go back
    #2 months
    #mainly tests if the program is capable of handling loading streak of videos
    #and stopping at the proper known id
    def testNormalWhereUserHasnotUsedProgram2MonthsDefaultSettings(self):
        self.clearDB()
        cursor = self.testing_connection.cursor()
        add_videos = """
            INSERT INTO KnownVideos (handle, known_id) VALUES
            ('RomanianTvee', 'Gg5DObWXubE'),
            ('an0nymooose', 'RzNkY1_Nk3o'),
            ('WillTennyson', '5yNESTDTUpg'),
            ('TechnologyConnections', 'kTctVqjhDEw'),
            ('thedoubtfultechnician', '-lhWtTY7kPQ')
        """
        cursor.execute(add_videos)
        self.testing_connection.commit()

        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/videos.txt"]
        nosub.main()

        #24 from RomanianTvee
        #6 from WillTennyson
        #0 from an0nymooose
        #2 from TechnologyConnections
        #2 from thedoubtfultechnician
        self.assertEqual(self.mock_browser.call_count, 42)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=pqYu8-JjXNQ"), #RTV first id seen
            call("https://www.youtube.com/watch?v=W2DdVFeq1WM"), #RTV
            call("https://www.youtube.com/watch?v=dyFCyOWq8PY"), #RTV
            call("https://www.youtube.com/watch?v=3W0yMU06_pY"), #RTV
            call("https://www.youtube.com/watch?v=wyf_za8nQDw"), #RTV
            call("https://www.youtube.com/watch?v=tZ1_HM2UtM8"), #RTV
            call("https://www.youtube.com/watch?v=PRZSddxEXwA"), #RTV
            call("https://www.youtube.com/watch?v=CRuqkK7wRxg"), #RTV
            call("https://www.youtube.com/watch?v=YOYNcGFZJhg"), #RTV
            call("https://www.youtube.com/watch?v=AO0kkIPov4I"), #RTV
            call("https://www.youtube.com/watch?v=oYAlnz2N4S0"), #RTV
            call("https://www.youtube.com/watch?v=Y8x9DzeKcXI"), #RTV
            call("https://www.youtube.com/watch?v=vwjZ7kYlc3I"), #RTV
            call("https://www.youtube.com/watch?v=L1ZZo4uZJ44"), #RTV
            call("https://www.youtube.com/watch?v=v9e77EYTHdM"), #RTV
            call("https://www.youtube.com/watch?v=dGAvFmVhU5c"), #RTV
            call("https://www.youtube.com/watch?v=OW_aVhwoaiQ"), #RTV
            call("https://www.youtube.com/watch?v=36CHAzlDXkY"), #RTV
            call("https://www.youtube.com/watch?v=e8StviDE3ms"), #RTV
            call("https://www.youtube.com/watch?v=oOgsIytfDAU"), #RTV
            call("https://www.youtube.com/watch?v=Rtbu_gIYP4A"), #RTV
            call("https://www.youtube.com/watch?v=DG8Gh1jxTiM"), #RTV
            call("https://www.youtube.com/watch?v=QV4H8HqUzZI"), #RTV
            call("https://www.youtube.com/watch?v=Jdloauunvlg"), #RTV
            call("https://www.youtube.com/watch?v=P0CJ8sCUyoY"), #RTV
            call("https://www.youtube.com/watch?v=oLqhEcpXN3g"), #RTV
            call("https://www.youtube.com/watch?v=KPhXm2LcTLM"), #RTV
            call("https://www.youtube.com/watch?v=sThB6Tw2zyI"), #RTV
            call("https://www.youtube.com/watch?v=tJkTVh4lkxk"), #RTV
            call("https://www.youtube.com/watch?v=uvG7jc4OUrA"), #RTV
            call("https://www.youtube.com/watch?v=T3d-c1TAQQg"), #Tennyson first id seen
            call("https://www.youtube.com/watch?v=lFzccuoS3ag"), #Tennyson
            call("https://www.youtube.com/watch?v=Y3oXlvHhdsk"), #Tennyson
            call("https://www.youtube.com/watch?v=kxYI20JV3O8"), #Tennyson
            call("https://www.youtube.com/watch?v=kIWXzXLkau4"), #Tennyson
            call("https://www.youtube.com/watch?v=eQTcMErJbxI"), #Tennyson
            call("https://www.youtube.com/watch?v=QEJpZjg8GuA"), #Tech Connect first id seen
            call("https://www.youtube.com/watch?v=HnMuNCl7tZ8"), #Tech Connect
            call("https://www.youtube.com/watch?v=fq--H6KvqUg"), #doubt tech first id seen
            call("https://www.youtube.com/watch?v=o5FQH7LxpU8"), #doubt tech
            call("https://www.youtube.com/watch?v=H3eIKQz1ISs"), #doubt tech
            call("https://www.youtube.com/watch?v=1yGlS-TjVJs"), #doubt tech
        ]
        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()

    #With RomanianTvee doing many daily uploads it mostly tests if it'll stop
    #at the known id even if it's within the time frame to be loaded
    #also tests from doubtful technician if it'll load a video from an unknown handle within the time frame
    def testNormalWhereTimeFrameGivenAndSomeData(self):
        self.clearDB()
        cursor = self.testing_connection.cursor()
        #RTV from 3 days ago
        add_videos = """
            INSERT INTO KnownVideos (handle, known_id) VALUES
            ('RomanianTvee', 'tZ1_HM2UtM8'),
            ('an0nymooose', 'RzNkY1_Nk3o'),
            ('WillTennyson', 'lFzccuoS3ag')
        """
        cursor.execute(add_videos)
        self.testing_connection.commit()

        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/videos.txt", "-t", "7", "days"]
        nosub.main()

        #5 from RomanianTvee -> update id pqYu8-JjXNQ
        #1 from WillTennyson -> update id T3d-c1TAQQg
        #0 from an0nymooose
        #1 from TechnologyConnections
        #1 from thedoubtfultechnician
        self.assertEqual(self.mock_browser.call_count, 8)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=pqYu8-JjXNQ"), #RTV first id seen
            call("https://www.youtube.com/watch?v=W2DdVFeq1WM"), #RTV
            call("https://www.youtube.com/watch?v=dyFCyOWq8PY"), #RTV
            call("https://www.youtube.com/watch?v=3W0yMU06_pY"), #RTV
            call("https://www.youtube.com/watch?v=wyf_za8nQDw"), #RTV
            call("https://www.youtube.com/watch?v=T3d-c1TAQQg"), #Will Tenny
            call("https://www.youtube.com/watch?v=fq--H6KvqUg"), #doubt tech
            call("https://www.youtube.com/watch?v=QEJpZjg8GuA"), #Tech Connect
        ]
        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()

    #test if given a time frame without data in the database if it'll abide by
    #the given time frame. Perhaps someone needs to clear the database and still
    #wants to load some videos within a time frame they know about will get some videos
    def testNormalFreshWithTimeFrameDefaultSettings(self):
        self.clearDB()

        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/videos.txt", "-t", "7", "days"]
        nosub.main()

        #14 from RomanianTvee
        #1 from WillTennyson
        #0 from an0nymooose -> add id RzNkY1_Nk3o
        #1 from TechnologyConnections
        #1 from thedoubtfultechnician
        self.assertEqual(self.mock_browser.call_count, 18)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=pqYu8-JjXNQ"), #RTV first id seen
            call("https://www.youtube.com/watch?v=W2DdVFeq1WM"), #RTV
            call("https://www.youtube.com/watch?v=dyFCyOWq8PY"), #RTV
            call("https://www.youtube.com/watch?v=3W0yMU06_pY"), #RTV
            call("https://www.youtube.com/watch?v=wyf_za8nQDw"), #RTV
            call("https://www.youtube.com/watch?v=tZ1_HM2UtM8"), #RTV
            call("https://www.youtube.com/watch?v=PRZSddxEXwA"), #RTV
            call("https://www.youtube.com/watch?v=CRuqkK7wRxg"), #RTV
            call("https://www.youtube.com/watch?v=YOYNcGFZJhg"), #RTV
            call("https://www.youtube.com/watch?v=AO0kkIPov4I"), #RTV
            call("https://www.youtube.com/watch?v=oYAlnz2N4S0"), #RTV
            call("https://www.youtube.com/watch?v=Y8x9DzeKcXI"), #RTV
            call("https://www.youtube.com/watch?v=vwjZ7kYlc3I"), #RTV
            call("https://www.youtube.com/watch?v=L1ZZo4uZJ44"), #RTV
            call("https://www.youtube.com/watch?v=v9e77EYTHdM"), #RTV
            call("https://www.youtube.com/watch?v=QEJpZjg8GuA"), #Tech Connect first id seen
            call("https://www.youtube.com/watch?v=fq--H6KvqUg"), #doubt tech first id seen
            call("https://www.youtube.com/watch?v=T3d-c1TAQQg"), #Will Tenny
        ]
        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()


    #tests if max loads will mess up default behavior without a time frame on a fresh start
    def testNormalFromFreshStartWithDefaultSettingsSpecifyingMax(self):
        self.clearDB()
        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/videos.txt", "-n", "2"]
        nosub.main()
        self.assertEqual(self.mock_browser.call_count, 5)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=pqYu8-JjXNQ"), #rtv
            call("https://www.youtube.com/watch?v=RzNkY1_Nk3o"), #mooose
            call("https://www.youtube.com/watch?v=QEJpZjg8GuA"), #tech connect
            call("https://www.youtube.com/watch?v=fq--H6KvqUg"), #doubt tech
            call("https://www.youtube.com/watch?v=T3d-c1TAQQg")  #will tenny
        ]
        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()

    def testNormalWithMaxLoadsWithDataFrom2Months(self):
        self.clearDB()
        cursor = self.testing_connection.cursor()
        add_videos = """
            INSERT INTO KnownVideos (handle, known_id) VALUES
            ('RomanianTvee', 'Gg5DObWXubE'),
            ('an0nymooose', 'RzNkY1_Nk3o'),
            ('WillTennyson', '5yNESTDTUpg'),
            ('TechnologyConnections', 'kTctVqjhDEw'),
            ('thedoubtfultechnician', '-lhWtTY7kPQ')
        """
        cursor.execute(add_videos)
        self.testing_connection.commit()

        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/videos.txt", "-n", "2"]
        nosub.main()

        self.assertEqual(self.mock_browser.call_count, 8)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=pqYu8-JjXNQ"), #RTV first id seen
            call("https://www.youtube.com/watch?v=W2DdVFeq1WM"), #RTV
            call("https://www.youtube.com/watch?v=T3d-c1TAQQg"), #Tennyson first id seen
            call("https://www.youtube.com/watch?v=lFzccuoS3ag"), #Tennyson
            call("https://www.youtube.com/watch?v=QEJpZjg8GuA"), #Tech Connect first id seen
            call("https://www.youtube.com/watch?v=HnMuNCl7tZ8"), #Tech Connect
            call("https://www.youtube.com/watch?v=fq--H6KvqUg"), #doubt tech first id seen
            call("https://www.youtube.com/watch?v=o5FQH7LxpU8"), #doubt tech
        ]
        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()

    #tests if max loads will over rule time frame even at fresh
    def testNormalFreshWithTimeFrameAndMaxLoadsSetToOne(self):
        self.clearDB()

        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/videos.txt", "-t", "3", "weeks", "-n", "1"]
        nosub.main()

        self.assertEqual(self.mock_browser.call_count, 4)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=pqYu8-JjXNQ"), #RTV first id seen
            call("https://www.youtube.com/watch?v=QEJpZjg8GuA"), #Tech Connect first id seen
            call("https://www.youtube.com/watch?v=fq--H6KvqUg"), #doubt tech first id seen
            call("https://www.youtube.com/watch?v=T3d-c1TAQQg"), #Will Tenny
        ]
        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()

    def testNormalWithDataFrom2MonthsWithTimeFrameAndMaxLoads(self):
        self.clearDB()
        cursor = self.testing_connection.cursor()
        add_videos = """
            INSERT INTO KnownVideos (handle, known_id) VALUES
            ('RomanianTvee', 'Gg5DObWXubE'),
            ('an0nymooose', 'RzNkY1_Nk3o'),
            ('WillTennyson', '5yNESTDTUpg'),
            ('TechnologyConnections', 'kTctVqjhDEw'),
            ('thedoubtfultechnician', '-lhWtTY7kPQ')
        """
        cursor.execute(add_videos)
        self.testing_connection.commit()

        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/videos.txt", "-t", "3", "weeks", "-n", "2"]
        nosub.main()


        #2 from RomanianTvee -> update id pqYu8-JjXNQ
        #2 from WillTennyson -> update id T3d-c1TAQQg
        #0 from an0nymooose -> update id RzNkY1_Nk3o
        #2 from TechnologyConnections -> same id of QEJpZjg8GuA
        #2 from thedoubtfultechnician from default settings -> add id fq--H6KvqUg
        self.assertEqual(self.mock_browser.call_count, 8)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=pqYu8-JjXNQ"), #RTV first id seen
            call("https://www.youtube.com/watch?v=W2DdVFeq1WM"), #RTV
            call("https://www.youtube.com/watch?v=T3d-c1TAQQg"), #Tennyson first id seen
            call("https://www.youtube.com/watch?v=lFzccuoS3ag"), #Tennyson
            call("https://www.youtube.com/watch?v=QEJpZjg8GuA"), #Tech Connect first id seen
            call("https://www.youtube.com/watch?v=HnMuNCl7tZ8"), #Tech Connect
            call("https://www.youtube.com/watch?v=fq--H6KvqUg"), #doubt tech first id seen
            call("https://www.youtube.com/watch?v=o5FQH7LxpU8"), #doubt tech
        ]
        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()

    def testNormalWithNewLineFile(self):
        self.clearDB()
        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/newlines.txt",]
        nosub.main()
        self.assertEqual(self.mock_browser.call_count, 0)
        cursor = self.testing_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM KnownVideos")
        self.assertEqual(cursor.fetchone()[0], 0)

    def testNormalWithEmptyFile(self):
        self.clearDB()
        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/empty.txt"]
        nosub.main()
        self.assertEqual(self.mock_browser.call_count, 0)
        cursor = self.testing_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM KnownVideos")
        self.assertEqual(cursor.fetchone()[0], 0)

    #the /usr/bin/sh does have read permission for everyone
    def testNormalPassingABinary(self):
        self.clearDB()
        sys.argv = ["nosub.py", "-f", "/usr/bin/sh"]
        with self.assertRaises(UnicodeDecodeError):
            nosub.main()

        cursor = self.testing_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM KnownVideos")
        self.assertEqual(cursor.fetchone()[0], 0)

#releases are little different as they don't have a date when they were made
#so it will behave like the default behavior of videos
class ReleaseExecutionTesting(unittest.TestCase):
    releases_table = "KnownReleases"
    releases_tab = "releases"
    id_field = "known_id"

    @classmethod
    def setUpClass(cls):
        cls.testing_connection = sqlite3.connect("ReleaseExecutionTesting.db")
        cursor = cls.testing_connection.cursor()

        create_releases = """
        CREATE TABLE IF NOT EXISTS KnownReleases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handle varchar(30) UNIQUE NOT NULL,
            known_id varchar(41) UNIQUE NOT NULL
        );
        """

        #delete any existing data before adding new data
        delete_releases = "DELETE FROM KnownReleases"

        cursor.execute(create_releases)
        cursor.execute(delete_releases)

        cls.testing_connection.commit()

        file1 = open("./TestData/ExecutionHtmls/Neon_Nox_Releases.html", "rb")
        file2 = open("./TestData/ExecutionHtmls/Tom_Cardy_Releases.html", "rb")
        file3 = open("./TestData/ExecutionHtmls/Buddha_Trixie_Releases.html", "rb")
        file4 = open("./TestData/ExecutionHtmls/not_real.html", "rb")

        #conceptually there is no difference in videos vs releases in how it's extracted
        #but if the internals were to change this is here to catch it
        #no_content and loaded_home are also slightly different as no_content
        #will not have the title tag, but loading from the home page can still
        #have the title with none of the content
        cls.neon_nox = file1.read()
        cls.tom_cardy = file2.read()
        cls.buddha_trixie = file3.read()
        cls.tom_cardy_11111 = file4.read()

        file1.close()
        file2.close()
        file3.close()
        file4.close()

    @classmethod
    def tearDownClass(cls):
        cls.testing_connection.close()

    def setUp(self):
        self.patcher_request = patch("requests.get", side_effect = self.mockObtainHtmls)
        self.patcher_db_conn = patch("nosub.connectToDB", side_effect = self.mocked_connection)
        self.patcher_mock_browser = patch("webbrowser.open_new_tab")

        self.patcher_request.start()
        self.patcher_db_conn.start()
        self.mock_browser = self.patcher_mock_browser.start()

        self.mock_browser.return_value = None

    def tearDown(self):
        self.patcher_request.stop()
        self.patcher_db_conn.stop()
        self.patcher_mock_browser.stop()

    def mockObtainHtmls(self, *args, **kwargs):
        response = Response()
        if args[0] == "https://www.youtube.com/@NeonNox/releases":
            response.status_code = 200
            response._content = self.neon_nox

        elif args[0] == "https://www.youtube.com/@tomcardy1/releases":
            response.status_code = 200
            response._content = self.tom_cardy

        elif args[0] == "https://www.youtube.com/@tomcardy11111/releases":
            response.status_code = 404
            response._content = self.tom_cardy_11111

        elif args[0] == "https://www.youtube.com/@BuddhaTrixie/releases":
            response.status_code = 200
            response._content = self.buddha_trixie
        else:
            raise Exception(f"Mocked html elements did not get expected args. Got {args}")

        return response

    def mocked_connection(self):
        if not self.testing_connection:
            self.testing_connection = sqlite3.connect("ReleaseExecutionTesting.db")

        return self.testing_connection

    def clearDB(self):
        cursor = self.testing_connection.cursor()
        cursor.execute("DELETE FROM KnownReleases")
        self.testing_connection.commit()

    #despite any execution the most recent video should be in the db
    def verifyPostDB(self):
        cursor = self.testing_connection.cursor()
        neon_handle = "NeonNox"
        tom_handle = "tomcardy1"
        buddha_handle = "BuddhaTrixie"

        new_neon_id = "OLAK5uy_kH4jLV7RYNpdfuuVT529OLzvFdKPLyDcA"
        new_tom_id = "OLAK5uy_nEL-YhKpNaq6yOUM35XCywYdtEh35Lymc"
        new_buddha_id = "OLAK5uy_mIg7sAsw6VFdUtKzOxlOWfJ9NU4ueknQ0"

        with self.subTest(msg = f"Testing handle {neon_handle} is set to have id {new_neon_id}"):
            result = cursor.execute(f"SELECT COUNT(id) FROM {self.releases_table} WHERE {self.id_field} = '{new_neon_id}' AND handle = '{neon_handle}';")
            self.assertEqual(result.fetchone()[0], 1)

        with self.subTest(msg = f"Testing handle {tom_handle} is set to have id {new_tom_id}"):
            result = cursor.execute(f"SELECT COUNT(id) FROM {self.releases_table} WHERE {self.id_field} = '{new_tom_id}' AND handle = '{tom_handle}';")
            self.assertEqual(result.fetchone()[0], 1)

        with self.subTest(msg = f"Testing handle {buddha_handle} is set to have id {new_buddha_id}"):
            result = cursor.execute(f"SELECT COUNT(id) FROM {self.releases_table} WHERE {self.id_field} = '{new_buddha_id}' AND handle = '{buddha_handle}';")
            self.assertEqual(result.fetchone()[0], 1)

    def testReleaseFromFreshStartWithDefaultSettings(self):
        self.clearDB()
        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/releases.txt", "-r"]
        nosub.main()
        self.assertEqual(self.mock_browser.call_count, 3)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=ePcdm5Vs8WQ&list=OLAK5uy_kH4jLV7RYNpdfuuVT529OLzvFdKPLyDcA"), #neon
            call("https://www.youtube.com/watch?v=BLzxuIfD9rU&list=OLAK5uy_nEL-YhKpNaq6yOUM35XCywYdtEh35Lymc"), #tom
            call("https://www.youtube.com/watch?v=Lmmfm_vya9Q&list=OLAK5uy_mIg7sAsw6VFdUtKzOxlOWfJ9NU4ueknQ0"), #buddha
        ]
        #order doesn't really matter if every is loaded that's fine
        #and that implies that it got everything in the file
        #it would also be annoying having to order the ids
        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()

    #Just checking if the verbose prints out
    #this doesn't really care if the program runs correctly but that verbosity is printed
    def testReleaseVerbose(self):
        self.clearDB()
        cursor = self.testing_connection.cursor()
        add_videos = """
            INSERT INTO KnownReleases (handle, known_id) VALUES
            ('NeonNox', 'OLAK5uy_kH4jLV7RYNpdfuuVT529OLzvFdKPLyDcA')
        """
        cursor.execute(add_videos)
        self.testing_connection.commit()

        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/verbose_release.txt", "-v", "-r"]
        #redirect output to a file
        with open("verbose_test_releases.txt", "w") as verbose_test:
            original_out = sys.stdout
            sys.stdout = verbose_test
            nosub.main()
            sys.stdout = original_out


        #read redirect file
        contents = ""
        with open("verbose_test_releases.txt", "r") as verbose_test:
            contents = verbose_test.read()
            self.assertTrue("checking handle NeonNox" in contents)
            self.assertTrue("checking handle tomcardy1" in contents)
            self.assertTrue("Loading URL https://www.youtube.com/watch?v=BLzxuIfD9rU&list=OLAK5uy_nEL-YhKpNaq6yOUM35XCywYdtEh35Lymc" in contents)
            self.assertTrue("No new releases for channel NeonNox" in contents)

    def testReleaseFromFreshStartWithMultipleFilesDefaultSettings(self):
        self.clearDB()
        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/releases_split_1.txt", "./TestFiles/ExecutionTesting/releases_split_2.txt", "-r"]
        nosub.main()
        self.assertEqual(self.mock_browser.call_count, 3)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=ePcdm5Vs8WQ&list=OLAK5uy_kH4jLV7RYNpdfuuVT529OLzvFdKPLyDcA"), #neon
            call("https://www.youtube.com/watch?v=BLzxuIfD9rU&list=OLAK5uy_nEL-YhKpNaq6yOUM35XCywYdtEh35Lymc"), #tom
            call("https://www.youtube.com/watch?v=Lmmfm_vya9Q&list=OLAK5uy_mIg7sAsw6VFdUtKzOxlOWfJ9NU4ueknQ0"), #buddha
        ]
        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()

    #test a streak of releases NeonNox
    #id already known tomcardy1
    #handle not known yet Buddha Trixie
    def testReleaseWithSomeDataInDatabaseDefaultSettings(self):
        self.clearDB()
        cursor = self.testing_connection.cursor()
        #tom cardy as no new content
        #neon nox as a streak of new releases
        #buddha trixies as new handle seen
        add_releases = """
            INSERT INTO KnownReleases (handle, known_id) VALUES
            ('NeonNox', 'OLAK5uy_kPHcvm3O4a4cTRlPfqlZh3btNIoxRWF4E'),
            ('tomcardy1', 'OLAK5uy_nEL-YhKpNaq6yOUM35XCywYdtEh35Lymc')
        """
        cursor.execute(add_releases)
        self.testing_connection.commit()

        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/releases.txt", "-r"]
        nosub.main()
        #2 from NeonNox
        #0 from TomCardy
        #1 from BuddhaTrixie
        self.assertEqual(self.mock_browser.call_count, 3)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=ePcdm5Vs8WQ&list=OLAK5uy_kH4jLV7RYNpdfuuVT529OLzvFdKPLyDcA"), #neon
            call("https://www.youtube.com/watch?v=vWw-lAQJuOk&list=OLAK5uy_lfpGH8uUFwOBDW7N7d1Mi9kbmavtBlz78"), #neon
            call("https://www.youtube.com/watch?v=Lmmfm_vya9Q&list=OLAK5uy_mIg7sAsw6VFdUtKzOxlOWfJ9NU4ueknQ0"), #buddha
        ]
        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()

    #sets database 2 releases behind
    def testReleaseWhereEachEntryWillLoad2PlaylistsDefaultSettings(self):
        self.clearDB()
        cursor = self.testing_connection.cursor()
        add_releases = """
            INSERT INTO KnownReleases (handle, known_id) VALUES
            ('NeonNox', 'OLAK5uy_kPHcvm3O4a4cTRlPfqlZh3btNIoxRWF4E'),
            ('tomcardy1', 'OLAK5uy_mFtIU1Yjyv7vaVR3nMaS__4fn3SDwSOWc'),
            ('BuddhaTrixie', 'OLAK5uy_lXGNChVf0HPaiNVZ9Ce6pD7aDvkn4gqIk')
        """
        cursor.execute(add_releases)
        self.testing_connection.commit()

        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/releases.txt", "-r"]
        nosub.main()

        #2 NeonNox
        #2 TomCardy
        #2 BuddhaTrixie
        self.assertEqual(self.mock_browser.call_count, 6)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=ePcdm5Vs8WQ&list=OLAK5uy_kH4jLV7RYNpdfuuVT529OLzvFdKPLyDcA"), #neon
            call("https://www.youtube.com/watch?v=vWw-lAQJuOk&list=OLAK5uy_lfpGH8uUFwOBDW7N7d1Mi9kbmavtBlz78"), #neon
            call("https://www.youtube.com/watch?v=BLzxuIfD9rU&list=OLAK5uy_nEL-YhKpNaq6yOUM35XCywYdtEh35Lymc"), #tom
            call("https://www.youtube.com/watch?v=GFokXnCCMf8&list=OLAK5uy_mWLLO29YLEChiYDDDWfVAZKOwG4eIiqkM"), #tom
            call("https://www.youtube.com/watch?v=Lmmfm_vya9Q&list=OLAK5uy_mIg7sAsw6VFdUtKzOxlOWfJ9NU4ueknQ0"), #buddha
            call("https://www.youtube.com/watch?v=JKg20el5TMg&list=OLAK5uy_mAZrwhX-YJxcRIXNT1lrFB34sN5kiosXU"), #buddha
        ]
        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()

    #time frame can't be used with releases
    def testReleaseWithTimeFrameGiven(self):
        self.clearDB()

        with self.assertRaises(SystemExit):
            sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/releases.txt", "-t", "7", "days", "-r"]
            nosub.main()

        self.assertEqual(self.mock_browser.call_count, 0)

    #since it's in default settings at fresh it should only load one video
    def testReleaseFromFreshStartWithDefaultSettingsSpecifyingMaxOf2(self):
        self.clearDB()
        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/releases.txt", "-n", "2", "-r"]
        nosub.main()
        self.assertEqual(self.mock_browser.call_count, 3)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=ePcdm5Vs8WQ&list=OLAK5uy_kH4jLV7RYNpdfuuVT529OLzvFdKPLyDcA"), #neon
            call("https://www.youtube.com/watch?v=BLzxuIfD9rU&list=OLAK5uy_nEL-YhKpNaq6yOUM35XCywYdtEh35Lymc"), #tom
            call("https://www.youtube.com/watch?v=Lmmfm_vya9Q&list=OLAK5uy_mIg7sAsw6VFdUtKzOxlOWfJ9NU4ueknQ0"), #buddha
        ]
        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()

    def testReleaseWithMaxLoadsSetAt2WithDifferingData(self):
        self.clearDB()
        cursor = self.testing_connection.cursor()
        #neon nox knows 2nd
        #tomcardy knows 3rd
        #buddha trixie knows 4th
        add_releases = """
            INSERT INTO KnownReleases (handle, known_id) VALUES
            ('NeonNox', 'OLAK5uy_lfpGH8uUFwOBDW7N7d1Mi9kbmavtBlz78'),
            ('tomcardy1', 'OLAK5uy_mFtIU1Yjyv7vaVR3nMaS__4fn3SDwSOWc'),
            ('BuddhaTrixie', 'OLAK5uy_kqq4KhPD_BoucnGGwAgBEAcQEEAH4GI18')
        """
        cursor.execute(add_releases)

        self.testing_connection.commit()

        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/releases.txt", "-n", "2", "-r"]
        nosub.main()

        #1 Neon Nox
        #2 Tom Cardy
        #2 Buddha Trixie
        self.assertEqual(self.mock_browser.call_count, 5)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=ePcdm5Vs8WQ&list=OLAK5uy_kH4jLV7RYNpdfuuVT529OLzvFdKPLyDcA"), #neon
            call("https://www.youtube.com/watch?v=BLzxuIfD9rU&list=OLAK5uy_nEL-YhKpNaq6yOUM35XCywYdtEh35Lymc"), #tom
            call("https://www.youtube.com/watch?v=GFokXnCCMf8&list=OLAK5uy_mWLLO29YLEChiYDDDWfVAZKOwG4eIiqkM"), #tom
            call("https://www.youtube.com/watch?v=Lmmfm_vya9Q&list=OLAK5uy_mIg7sAsw6VFdUtKzOxlOWfJ9NU4ueknQ0"), #buddha
            call("https://www.youtube.com/watch?v=JKg20el5TMg&list=OLAK5uy_mAZrwhX-YJxcRIXNT1lrFB34sN5kiosXU"), #buddha
        ]

        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()

    def testReleaseFreshWithTimeFrameAndMaxLoads(self):
        self.clearDB()

        with self.assertRaises(SystemExit):
            sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/releases.txt", "-t", "3", "weeks", "-n", "1", "-r"]
            nosub.main()

        self.assertEqual(self.mock_browser.call_count, 0)

    def testReleaseWithNewLineFile(self):
        self.clearDB()
        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/newlines.txt", "-r"]
        nosub.main()
        self.assertEqual(self.mock_browser.call_count, 0)
        cursor = self.testing_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM KnownVideos")
        self.assertEqual(cursor.fetchone()[0], 0)

    def testReleaseWithEmptyFile(self):
        self.clearDB()
        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/empty.txt", "-r"]
        nosub.main()
        self.assertEqual(self.mock_browser.call_count, 0)
        cursor = self.testing_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM KnownVideos")
        self.assertEqual(cursor.fetchone()[0], 0)

    #the /usr/bin/sh does have read permission for everyone
    def testReleasePassingABinary(self):
        self.clearDB()
        sys.argv = ["nosub.py", "-f", "/usr/bin/sh", "-r"]
        with self.assertRaises(UnicodeDecodeError):
            nosub.main()

        cursor = self.testing_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM KnownVideos")
        self.assertEqual(cursor.fetchone()[0], 0)

#since both execution is just calling normalExec and releaseExec
#it only needs to test if it'll get all the contents
class BothExecutionTesting(unittest.TestCase):
    releases_table = "KnownReleases"
    videos_table = "KnownVideos"

    releases_tab = "releases"
    videos_tab = "videos"
    id_field = "known_id"

    @classmethod
    def setUpClass(cls):
        cls.testing_connection = sqlite3.connect("BothExecutionTesting.db")
        cursor = cls.testing_connection.cursor()

        create_videos = """
        CREATE TABLE IF NOT EXISTS KnownVideos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handle varchar(30) UNIQUE NOT NULL,
            known_id varchar(11) UNIQUE NOT NULL
        );
        """

        create_releases = """
        CREATE TABLE IF NOT EXISTS KnownReleases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            handle varchar(30) UNIQUE NOT NULL,
            known_id varchar(41) UNIQUE NOT NULL
        );
        """

        #delete any existing data before adding new data
        delete_videos = "DELETE FROM KnownVideos"
        delete_releases = "DELETE FROM KnownReleases"

        cursor.execute(create_videos)
        cursor.execute(create_releases)

        cursor.execute(delete_releases)
        cursor.execute(delete_videos)

        cls.testing_connection.commit()

        file1 = open("./TestData/ExecutionHtmls/Long_Break_An0nymooose.html", "rb")
        file2 = open("./TestData/ExecutionHtmls/Many_Daily_Uploads_Romanian_Tvee.html", "rb")
        file3 = open("./TestData/ExecutionHtmls/7_Hour_Upload_Technology_Connections.html", "rb")
        file4 = open("./TestData/ExecutionHtmls/5_Day_Upload_The_Doubtful_Technician.html", "rb")
        file5 = open("./TestData/ExecutionHtmls/Changed_Their_Handle.html", "rb")
        file6 = open("./TestData/ExecutionHtmls/Weekly_Uploads_Will_Tennyson.html", "rb")
        file7 = open("./TestData/ExecutionHtmls/Neon_Nox_Releases.html", "rb")
        file8 = open("./TestData/ExecutionHtmls/Tom_Cardy_Releases.html", "rb")
        file9 = open("./TestData/ExecutionHtmls/Buddha_Trixie_Releases.html", "rb")
        file10 = open("./TestData/ExecutionHtmls/not_real.html", "rb")
        file11 = open("./TestData/ExecutionHtmls/home_page.html", "rb")
        #note that this home page is not associated with any of the youtubers
        #it doesn't really matter as you can not extract video or release information
        #from the home page so the program should detect this

        cls.anonymooose = file1.read()
        cls.romanian_tvee = file2.read()
        cls.technology_connections = file3.read()
        cls.doubtful_technician = file4.read()
        cls.change_handle = file5.read()
        cls.will_tennyson = file6.read()
        cls.neon_nox = file7.read()
        cls.tom_cardy = file8.read()
        cls.buddha_trixie = file9.read()
        cls.tom_cardy_11111 = file10.read()
        cls.home_page_redirect = file11.read()

        file1.close()
        file2.close()
        file3.close()
        file4.close()
        file5.close()
        file6.close()
        file7.close()
        file8.close()
        file9.close()
        file10.close()
        file11.close()

    @classmethod
    def tearDownClass(cls):
        cls.testing_connection.close()

    def setUp(self):
        self.patcher_request = patch("requests.get", side_effect = self.mockObtainHtmls)
        self.patcher_db_conn = patch("nosub.connectToDB", side_effect = self.mocked_connection)
        self.patcher_mock_browser = patch("webbrowser.open_new_tab")

        self.patcher_request.start()
        self.patcher_db_conn.start()
        self.mock_browser = self.patcher_mock_browser.start()

        self.mock_browser.return_value = None

    def tearDown(self):
        self.patcher_request.stop()
        self.patcher_db_conn.stop()
        self.patcher_mock_browser.stop()

    def mockObtainHtmls(self, *args, **kwargs):
        response = Response()
        if args[0] == "https://www.youtube.com/@an0nymooose/videos":
            response.status_code = 200
            response._content = self.anonymooose

        elif args[0] == "https://www.youtube.com/@TechnologyConnections/videos":
            response.status_code = 200
            response._content = self.technology_connections

        elif args[0] == "https://www.youtube.com/@RomanianTvee/videos":
            response.status_code = 200
            response._content = self.romanian_tvee

        elif args[0] == "https://www.youtube.com/@thedoubtfultechnician/videos":
            response.status_code = 200
            response._content = self.doubtful_technician

        elif args[0] == "https://www.youtube.com/@thedoubtfultechnician8067/videos":
            response.status_code = 404
            response._content = self.change_handle

        elif args[0] == "https://www.youtube.com/@WillTennyson/videos":
            response.status_code = 200
            response._content = self.will_tennyson

        elif args[0] == "https://www.youtube.com/@NeonNox/releases":
            response.status_code = 200
            response._content = self.neon_nox

        elif args[0] == "https://www.youtube.com/@tomcardy1/releases":
            response.status_code = 200
            response._content = self.tom_cardy

        elif args[0] == "https://www.youtube.com/@tomcardy11111/releases":
            response.status_code = 404
            response._content = self.tom_cardy_11111

        elif args[0] == "https://www.youtube.com/@BuddhaTrixie/releases":
            response.status_code = 200
            response._content = self.buddha_trixie
        else:
            response.status_code = 200
            response._content = self.home_page_redirect

        return response

    def mocked_connection(self):
        if not self.testing_connection:
            self.testing_connection = sqlite3.connect("BothExecutionTesting.db")

        return self.testing_connection

    def clearDB(self):
        cursor = self.testing_connection.cursor()
        cursor.execute("DELETE FROM KnownReleases")
        cursor.execute("DELETE FROM KnownVideos")
        self.testing_connection.commit()

    def verifyPostDB(self):
        cursor = self.testing_connection.cursor()
        rtv_handle = "RomanianTvee"
        mooose_handle = "an0nymooose"
        tech_connection_handle = "TechnologyConnections"
        doubt_tech_handle = "thedoubtfultechnician"
        will_tenny_handle = "WillTennyson"
        neon_handle = "NeonNox"
        tom_handle = "tomcardy1"
        buddha_handle = "BuddhaTrixie"

        new_rtv_id = "pqYu8-JjXNQ"
        new_will_tenny_id = "T3d-c1TAQQg"
        new_tech_connection_id = "QEJpZjg8GuA"
        new_mooose_id = "RzNkY1_Nk3o"
        new_doubt_tech_id = "fq--H6KvqUg"
        new_neon_id = "OLAK5uy_kH4jLV7RYNpdfuuVT529OLzvFdKPLyDcA"
        new_tom_id = "OLAK5uy_nEL-YhKpNaq6yOUM35XCywYdtEh35Lymc"
        new_buddha_id = "OLAK5uy_mIg7sAsw6VFdUtKzOxlOWfJ9NU4ueknQ0"

        with self.subTest(msg = f"Testing handle {rtv_handle} is set to have id {new_rtv_id}"):
            result = cursor.execute(f"SELECT COUNT(id) FROM {self.videos_table} WHERE {self.id_field} = '{new_rtv_id}' AND handle = '{rtv_handle}';")
            self.assertEqual(result.fetchone()[0], 1)

        with self.subTest(msg = f"Testing handle {will_tenny_handle} is set to have id {new_will_tenny_id}"):
            result = cursor.execute(f"SELECT COUNT(id) FROM {self.videos_table} WHERE {self.id_field} = '{new_will_tenny_id}' AND handle = '{will_tenny_handle}';")
            self.assertEqual(result.fetchone()[0], 1)

        with self.subTest(msg = f"Testing handle {tech_connection_handle} is set to have id {new_tech_connection_id}"):
            result = cursor.execute(f"SELECT COUNT(id) FROM {self.videos_table} WHERE {self.id_field} = '{new_tech_connection_id}' AND handle = '{tech_connection_handle}';")
            self.assertEqual(result.fetchone()[0], 1)

        with self.subTest(msg = f"Testing handle {mooose_handle} is set to have id {new_mooose_id}"):
            result = cursor.execute(f"SELECT COUNT(id) FROM {self.videos_table} WHERE {self.id_field} = '{new_mooose_id}' AND handle = '{mooose_handle}';")
            self.assertEqual(result.fetchone()[0], 1)

        with self.subTest(msg = f"Testing handle {doubt_tech_handle} is set to have id {new_doubt_tech_id}"):
            result = cursor.execute(f"SELECT COUNT(id) FROM {self.videos_table} WHERE {self.id_field} = '{new_doubt_tech_id}' AND handle = '{doubt_tech_handle}';")
            self.assertEqual(result.fetchone()[0], 1)

        with self.subTest(msg = f"Testing handle {neon_handle} is set to have id {new_neon_id}"):
            result = cursor.execute(f"SELECT COUNT(id) FROM {self.releases_table} WHERE {self.id_field} = '{new_neon_id}' AND handle = '{neon_handle}';")
            self.assertEqual(result.fetchone()[0], 1)

        with self.subTest(msg = f"Testing handle {tom_handle} is set to have id {new_tom_id}"):
            result = cursor.execute(f"SELECT COUNT(id) FROM {self.releases_table} WHERE {self.id_field} = '{new_tom_id}' AND handle = '{tom_handle}';")
            self.assertEqual(result.fetchone()[0], 1)

        with self.subTest(msg = f"Testing handle {buddha_handle} is set to have id {new_buddha_id}"):
            result = cursor.execute(f"SELECT COUNT(id) FROM {self.releases_table} WHERE {self.id_field} = '{new_buddha_id}' AND handle = '{buddha_handle}';")
            self.assertEqual(result.fetchone()[0], 1)

    def testBothExecutionFreshDefault(self):
        self.clearDB()
        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/both.txt", "-b"]
        nosub.main()
        self.assertEqual(self.mock_browser.call_count, 8)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=pqYu8-JjXNQ"), #rtv
            call("https://www.youtube.com/watch?v=RzNkY1_Nk3o"), #mooose
            call("https://www.youtube.com/watch?v=QEJpZjg8GuA"), #tech connect
            call("https://www.youtube.com/watch?v=fq--H6KvqUg"), #doubt tech
            call("https://www.youtube.com/watch?v=T3d-c1TAQQg"), #will tenny
            call("https://www.youtube.com/watch?v=ePcdm5Vs8WQ&list=OLAK5uy_kH4jLV7RYNpdfuuVT529OLzvFdKPLyDcA"), #neon
            call("https://www.youtube.com/watch?v=BLzxuIfD9rU&list=OLAK5uy_nEL-YhKpNaq6yOUM35XCywYdtEh35Lymc"), #tom
            call("https://www.youtube.com/watch?v=Lmmfm_vya9Q&list=OLAK5uy_mIg7sAsw6VFdUtKzOxlOWfJ9NU4ueknQ0"), #buddha
        ]
        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()

    #Releases don't use the time frame, but videos do
    def testBothFreshWithTimeFrameDefault(self):
        self.clearDB()
        sys.argv = ["nosub.py", "-f", "./TestFiles/ExecutionTesting/both.txt", "-b", "-t", "2", "days"]
        nosub.main()
        self.assertEqual(self.mock_browser.call_count, 9)
        call_list =\
        [
            call("https://www.youtube.com/watch?v=pqYu8-JjXNQ"), #rtv
            call("https://www.youtube.com/watch?v=W2DdVFeq1WM"), #rtv
            call("https://www.youtube.com/watch?v=dyFCyOWq8PY"), #rtv
            call("https://www.youtube.com/watch?v=3W0yMU06_pY"), #rtv
            call("https://www.youtube.com/watch?v=wyf_za8nQDw"), #rtv
            call("https://www.youtube.com/watch?v=QEJpZjg8GuA"), #tech connect
            call("https://www.youtube.com/watch?v=ePcdm5Vs8WQ&list=OLAK5uy_kH4jLV7RYNpdfuuVT529OLzvFdKPLyDcA"), #neon
            call("https://www.youtube.com/watch?v=BLzxuIfD9rU&list=OLAK5uy_nEL-YhKpNaq6yOUM35XCywYdtEh35Lymc"), #tom
            call("https://www.youtube.com/watch?v=Lmmfm_vya9Q&list=OLAK5uy_mIg7sAsw6VFdUtKzOxlOWfJ9NU4ueknQ0"), #buddha
        ]
        self.mock_browser.assert_has_calls(call_list, any_order = True)
        self.verifyPostDB()

if __name__ == '__main__':
    unittest.main()
