'''
    Wrapper around stepic API
'''
import json
import multiprocessing
import sys
import traceback
from typing import List

import asyncio
import aiohttp
import json
import requests
import requests.auth

# STEPIC_URL = "https://stepic.org/api"
# APP_FOLDER = ".stepic"
# CLIENT_FILE = APP_FOLDER + "/client_file"
# ATTEMPT_FILE = APP_FOLDER + "/attempt_file"


class Progress:
    def __init__(self, data: dict):
        # print(data)
        self.id = data['id']
        self.score = data['score']
        self.cost = data['cost']
        self.n_steps = data['n_steps']
        self.n_steps_passed = data['n_steps_passed']
        self.is_passed = data['is_passed']

    # set progress object for course, steps, lessons and other stuff
    @staticmethod
    def _static_set_progress_for_instance(instance, stepicClient):
        if instance._progress_id is not None and stepicClient is not None:
            progress_dict = stepicClient._get_request_api(
                "progresses/{}".format(instance._progress_id), prms={})[
                'progresses'][0]
            # print(progress_dict)
            return Progress(progress_dict)
        else:
            return None


class Course:
    def __init__(self, decoded_data: dict, stepicClient):
        self.id = decoded_data['id']
        self.title = decoded_data['title']
        self._section_ids = decoded_data['sections']

        self._progress_id = decoded_data['progress']
        self.progress = Progress._static_set_progress_for_instance(self,
                                                                   stepicClient)
        # todo SCORE FOR IT
        # todo grab more data


class Lesson:
    def __init__(self, decoded_data: dict, progr: Progress):
        self.id = decoded_data['id']
        self.title = decoded_data['title']

        self._steps_ids = decoded_data['steps']
        # todo grab more data

        self._progress_id = decoded_data['progress']
        self.progress = progr


class Section:
    def __init__(self, decoded_data: dict, lesson_list: List[Lesson],
                 stepicClient):
        self.id = decoded_data['id']
        self.title = decoded_data['title']
        self.hard_deadline = decoded_data['hard_deadline']
        self.soft_deadline = decoded_data['soft_deadline']

        self.lesson_list = lesson_list

        # todo SCORE FOR IT
        self._progress_id = decoded_data['progress']
        self.progress = Progress._static_set_progress_for_instance(self,
                                                                   stepicClient)


class Video:
    def __init__(self, video_dict):
        self.id = video_dict['id']
        self.thumbnail = video_dict['thumbnail']
        self.urls = {}
        for dct in video_dict['urls']:
            self.urls[dct['quality']] = dct['url']


class Block:
    def __init__(self, block_dict):
        self.name = block_dict['name']
        self.text = block_dict['text']
        if block_dict['video'] is not None:
            self.video = Video(block_dict['video'])
        else:
            self.video = None

        self.animation = block_dict['animation']  # : null,
        self.options = block_dict['options']  # {},
        self.subtitle_files = block_dict['subtitle_files']  #


class Step:
    def __init__(self, steps_data: dict, stepicClient=None):
        self.id = steps_data['id']
        self.lesson = steps_data['lesson']
        self._block = Block(steps_data['block'])  # from api

        self.type = self._block.name  # str, 'video' or others
        self.code_options = self._block.options if self.type == "code" else \
            None
        self.video = self._block.video
        self.text = self._block.text

        self._progress_id = steps_data['progress']
        self.progress = Progress._static_set_progress_for_instance(self,
                                                                   stepicClient)


class Attempt:
    def __init__(self, steps_data: dict):
        self.id = steps_data['id']
        self.dataset = steps_data['dataset']  # dict with task data
        self.dataset_url = steps_data['dataset_url']
        self.step_id = steps_data['step']
        self.user_id = steps_data['user']
        self.time = steps_data['time']
        # todo parse dataset, it can be different


class Submission:
    def __init__(self, data: dict):
        self.id = data['id']  # :: int
        self.status = data['status']  # :: str
        self.score = data['score']  # :: int
        self.reply = data['reply']  # :: dict
        self.attempt_id = data['attempt']
        self.time = data['time']


class Task:
    task_types = [
        'matching',
        'math',
        'sorting',
        'number',
        'free-answer',
        'table',
        'sorting',
        'choice',
        'code',
    ]

    def __init__(self, step: Step, last_attempt: Attempt,
                 last_submission: Submission):
        # todo do all stuff
        pass
        # self.type
        # self.step_text
        # self.


class StepicClient:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = self._get_token()
        self.API_URL_BASE = "https://stepik.org:443/api/"

    def close(self):
        pass
        # self._loop.run_until_complete(asyncio.sleep(0))
        # self._loop.close()
        # self._client_session.close()

    def _get_token(self):
        auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
        resp = requests.post('https://stepik.org/oauth2/token/',
                             data={
                                 'grant_type': 'client_credentials',
                             },
                             auth=auth)
        token = json.loads(resp.text)['access_token']
        return token

    # not used
    def _get_request_api(self, api_url_end: str, prms: dict) -> \
            dict:
        data = json.loads(
            requests.get('https://stepik.org:443/api/' + api_url_end,
                         headers={'Authorization': 'Bearer ' + self.token},
                         params=prms
                         ).text
        )
        return data

    def _get2_content_from_all_pages(self, api_name: str, params: dict) -> \
            List[dict]:
        pageNum = 0
        hasNextPage = True
        accumulator_list = []

        try:
            while hasNextPage:
                pageNum += 1
                params['page'] = pageNum
                pageContent = self._get_request_api(api_name, params)
                hasNextPage = pageContent['meta']['has_next']
                contents = pageContent[api_name]

                accumulator_list.extend(contents)

            return accumulator_list

        except Exception:
            traceback.print_exc(file=sys.stderr)
            print("Error exception: something was broken!")

    def __get_progress_ids(self, instances: List[dict]):
        progress_ids = []
        for dct in instances:
            progress_ids.append(dct['progress'])
        return progress_ids

    ##########################################################################
    # UNUSED
    def _get_sections_by_course_id(self, course_id: int) -> List[Section]:
        course = self._get_course_by_course_id(course_id)

        sections = []
        for sect_id in course._section_ids:
            sec_data = self._get_request_api(
                "sections/{}".format(sect_id), {})
            sections.append(Section(sec_data['sections'][0], [], self))

        return sections

    # steps information
    def _get_step_by_step_id(self, step_id: int) -> Step:
        step_data = json.loads(
            requests.get('https://stepik.org:443/api/steps/{}'.format(step_id),
                         headers={
                             'Authorization': 'Bearer ' + self.token}).text)

        return Step(step_data['steps'][0])

    # return Course
    def _get_course_by_course_id(self, course_id: int) -> Course:
        data = self._get_request_api(
            "courses/{}".format(course_id), {})
        course = Course(data['courses'][0], self)
        return course

    def _get_lesson(self, lesson_id: int) -> Lesson:
        lesson_dict = self._get_request_api(
            "lessons/{}".format(lesson_id), {})['lessons'][0]
        progress_id = lesson_dict['progress']
        return Lesson(lesson_dict,
                      self._get_progress_by_progress_id(progress_id))

    ##########################################################################

    # return [Course]
    def get_user_courses(self) -> List[Course]:
        courses_dicts = self._get2_content_from_all_pages(
            "courses", params={'enrolled': 'PWNED'})
        courses = []
        for course_dict in courses_dicts:
            course = Course(course_dict, self)
            courses.append(course)
        return courses

    def _requests_url(self, urls: List[str]) -> List[dict]:
        async def get_json(loop, url):
            async with aiohttp.ClientSession(
                    loop=loop,
                    headers={'Authorization': 'Bearer ' + self.token}
            ) as client_session:
                async with client_session.get(url) as response:
                    return await response.read()

        loop = asyncio.get_event_loop()
        result_jsons = loop.run_until_complete(
            asyncio.gather(
                *[get_json(loop, url) for url in urls]
            )
        )
        loop.run_until_complete(asyncio.sleep(0))
        loop.close()

        dicts = []
        for json_str in result_jsons:
            dicts.append(json.loads(json_str))
        return dicts

    # return  [Lesson]
    def get_lessons_by_course_id(self, course_id: int) -> List[Lesson]:
        lessons_dicts = self._get2_content_from_all_pages(
            "lessons", params={'course': course_id}
        )

        progress_ids = self.__get_progress_ids(lessons_dicts)
        urls = ["{}{}{}".format(self.API_URL_BASE, "progresses/", progress_id)
                for progress_id in progress_ids]

        async def get_json(loop, url):
            async with aiohttp.ClientSession(
                    loop=loop,
                    headers={'Authorization': 'Bearer ' + self.token}
            ) as client_session:
                async with client_session.get(url) as response:
                    return await response.read()

        loop = asyncio.get_event_loop()
        progress_jsons = loop.run_until_complete(
            asyncio.gather(
                *[get_json(loop, url) for url in urls]
            )
        )
        loop.run_until_complete(asyncio.sleep(0))
        loop.close()

        lessons = []
        progr_ix = 0
        for lesson_dict in lessons_dicts:
            progr = Progress(
                json.loads(progress_jsons[progr_ix])['progresses'][0])
            progr_ix += 1
            lessons.append(Lesson(lesson_dict, progr))

        return lessons

    # SO SLOW
    def get_sections(self, course_id: int) -> List[Section]:
        course = self._get_course_by_course_id(course_id)

        lessons = self.get_lessons_by_course_id(course_id)
        all_lessons_dict = {}
        for les in lessons:
            all_lessons_dict[les.id] = les

        units_dicts_list = self._get2_content_from_all_pages(
            "units", {"course": course_id})
        units_dict = {}
        for dct in units_dicts_list:
            units_dict[dct['id']] = dct

        ######
        # progress_ids = self.__get_progress_ids(lessons_dicts)
        # urls = ["{}{}{}".format(self.API_URL_BASE, "progresses/", progress_id)
        #         for progress_id in progress_ids]

        ######
        sections = []
        for section_id in course._section_ids:  # load every section
            section_dict = self._get_request_api(
                "sections/{}".format(section_id), {})['sections'][0]
            unit_ids = section_dict['units']

            lesson_list = []

            for unit_id in unit_ids:
                lesson_id = units_dict[unit_id]['lesson']
                lesson_list.append(all_lessons_dict[lesson_id])

            sections.append(Section(section_dict, lesson_list, self))

        return sections

    def get_step_by_lesson_id(self, lesson_id: int) -> List[Step]:
        lesson = self._get_lesson(lesson_id)
        steps = []
        for step_id in lesson._steps_ids:
            steps.append(self._get_step_by_step_id(step_id))
        return steps

    def get_step_text(self, step_id: int) -> str:
        step = self._get_step_by_step_id(step_id)
        return step.text

    def get_step_video(self, step_id: int) -> Video:
        step = self._get_step_by_step_id(step_id)
        return step.video

    ##### FUTURE #################################################
    # task info, NOT submissions here

    def _get_task_by_step_id(self, step_id: int):  # -> Task:
        step = self._get_step_by_step_id(step_id)
        last_attempt = self._get_last_attempt_by_step_id(step_id)
        if last_attempt is not None:
            last_submission = self._get_last_submission_by_step_id(step_id)
            return Task(step, last_attempt, last_submission)
        return None

    def _get_last_attempt_by_step_id(self, step_id: int):  # -> Attempt:
        data = self._get_request_api("attempts",
                                     {'step': str(step_id)})

        if len(data['attempts']) > 0:
            return Attempt(data['attempts'][0])
        else:
            return None

    def _get_all_attempt_by_step_id(self, step_id: int):  # -> Attempt:
        data = self._get_request_api("attempts",
                                     {'step': str(step_id)})

        if len(data['attempts']) > 0:
            return Attempt(data['attempts'][0])
        else:
            return None

    def _get_last_submission_by_step_id(self, step_id: int):
        data = self._get_request_api("submissions",
                                     {'step': str(step_id)})

        if len(data['attempts']) > 0:
            return Submission(data['submissions'][0])
        else:
            return None

    def _get_progress_by_progress_id(self, progress_id: str) -> Progress:
        data = self._get_request_api("progresses/{}".format(progress_id), {})
        return Progress(data['progresses'][0])

    def send_solution(self, step_id: int, data: str, params = "") \
    -> (str, str):
        import time
        step = self._get_step_by_step_id(step_id)
        type = step.type
        if step.type == 'text':
            raise ValueError('Step %d is textual, with no tasks' % step_id)
        elif step.type == 'video':
            raise ValueError('Step %d is a video and has no tasks' % step_id)
        elif step.type == 'string':
            reply = {
                'text' : data,
                'files' : []
            }
        elif step.type == 'math':
            reply = {
                'formula' : data,
            }
        elif step.type == 'number':
            reply = {
                'number' : float(data),
            }
        elif step.type == 'free-answer':
            reply = {
                'attachments' : [],
                'text' : data
            }
        elif step.type == 'choice':
            reply = {
                'choices' : list(map(lambda x : True if x else False,
                                     data.split()))
            }
        elif step.type == 'code':
            reply = {
                'language': params,
                'code': data,
            }
        elif step.type == 'sorting' or step.type == 'matching':
            ords = list(map(lambda x : int(x), data.split()))
            mn = min(ords)
            reply = {
                'ordering': list(map(lambda x : x - mn, ords))
            }
        else:
            raise ValueError('Unsupported step type %s' % type)
        attempts = self._get_request_api("attempts", {'step': str(step_id)})
        current_time = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
        if len(attempts['attempts']):
            attempt_id = attempts['attempts'][-1]['id']
        else:
            attempt = { 'attempt' : {
                "time": current_time,
                "step": step.id
            } }
            rs = requests.post('https://stepik.org:443/api/' + 'attempts',
                             headers={'Authorization': 'Bearer ' + self.token},
                             json=attempt).text
            nattempt = json.loads(rs)['attempts'][0]
            attempt_id = nattempt['id']
        submission = {
            "submission" : {
                "time" : current_time,
                "reply" : reply,
                "attempt" : attempt_id
            }
        }
        rs = requests.post('https://stepik.org:443/api/' + 'submissions',
                         headers={'Authorization': 'Bearer ' + self.token},
                         json=submission).text
        nsubmission = json.loads(rs)['submissions'][0]
        submission_id = nsubmission['id']
        while nsubmission['status'] == 'evaluation':
            eta = nsubmission['eta']
            time.sleep(eta)
            nsubmission = self._get_request_api("submissions/" + str(submission_id), {})['submissions'][0]
        return (nsubmission['status'], nsubmission['hint'], nsubmission['feedback'])



def main():
    client = StepicClient(CLIENT_ID, CLIENT_SECRET)
    # # Print all courses for this users
    # elems = client.get_user_courses()
    # for elem in elems:
    #     print("## Id = {} with title: '{}'".format(
    #         elem.id, elem.title))

    # # Printing all lessons
    # elems = client.get_lessons_by_course_id(125)
    # for elem in elems:
    #     print("## Id = {} with title: '{}'".format(
    #         elem.id, elem.title))

    # # Example of getting video url
    # step = client.get_steps(170472)
    # print(step.block.video.urls['360'])

    # # example of printing section names for course
    # sections = client.get_sections_by_course_id(125)
    # for sec in sections:
    #     print(sec.title)

    # # get secions by course id - SLOW SLOW
    sections = client.get_sections(3089)
    for sect in sections:
        print("## [{}/{}] Id = {} with title: '{}'".format(
            sect.progress.score, sect.progress.cost, sect.id, sect.title))
        for lesson in sect.lesson_list:
            print("## \t lesson: {}".format(lesson.title))

    # # print step info by lesson_id
    # steps = client.get_step_by_lesson_id(9538)
    # for step in steps:
    #     print("## Id = {} with title: '{}'".format(
    #         step.id, step.type))

    # # get text by step example
    # print(client.get_step_text(170460))

    # # get video example
    # video = client.get_step_video(206143)
    # print(video.urls['1080'])

    # print(client.get_step_text(280213))

    # steps = [
    #     320635,
    #     321365,
    #     321364,
    #     321626,
    #     321627,
    #     321629,
    #     321628,
    #     321630,
    #     321631
    # ]
    # # example of printing all attempts
    # for step_id in steps:
    #     attempts = client._get_attempts_by_step_id(step_id)
    #     for att in attempts:
    #         print(att.dataset)
    #         print()

    # lessons = client.get_lessons_by_course_id(3089)
    # for les in lessons:
    #     print("{} {} {}".format(les.title, les.id, les.progress.id))
    # client.get_step_by_lesson_id(48688)
    # print(client._get_progress_by_progress_id('76-48688'))
    client.close()


def test_trash():
    client = StepicClient(CLIENT_ID, CLIENT_SECRET)
    params = {
        'course': 1780
    }
    lst = client._get2_content_from_all_pages("units", params)
    for elem in lst:
        print(elem)
        print()


if __name__ == '__main__':
    main()
    # test_trash()
