'''
    Wrapper around stepic API
'''
import asyncio
import json
import sys
import traceback
from typing import Optional

import aiohttp
import requests
import requests.auth

from stepik.stepik_objects import *


class StepicClient:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self._impl = StepicClientImpl(client_id, client_secret)
        self.API_URL_BASE = "https://stepik.org:443/api/"

    def close(self):
        self._impl.close()

    # ####################################################

    def get_lessons_by_course_id(self, course_id: int) -> List[Lesson]:
        lessons_dicts = self._impl._get_content_from_all_pages(
            "lessons", params={'course': course_id}
        )

        progresses = self._impl._gen_progresses_from_items(lessons_dicts)

        lessons = [Lesson(lesson_dict, progr) for lesson_dict, progr in
                   list(zip(lessons_dicts, progresses))]

        return lessons

    # SLOW, could be faster
    def get_sections(self, course_id: int) -> List[Section]:
        course = self._impl._get_course_by_course_id(course_id)

        lessons = self.get_lessons_by_course_id(course_id)
        all_lessons_dict = {}
        for les in lessons:
            all_lessons_dict[les.id] = les

        units_dicts_list = self._impl._get_content_from_all_pages(
            "units", {"course": course_id})
        units_dict = {}
        for dct in units_dicts_list:
            units_dict[dct['id']] = dct

        ###### NEW CODE
        get_sections_urls = self._impl._gen_urls('sections',
                                                 course._section_ids)
        section_dicts = self._impl._requests_url_async(get_sections_urls,
                                                       "sections")
        progresses = self._impl._gen_progresses_from_items(section_dicts)

        sections = []
        for section_dict, progr in (
                list(zip(section_dicts, progresses))):
            unit_ids = section_dict['units']
            lesson_list = []

            for unit_id in unit_ids:
                lesson_id = units_dict[unit_id]['lesson']
                lesson_list.append(all_lessons_dict[lesson_id])

            sections.append(Section(section_dict, lesson_list, progr))

        ###### OLD CODE
        # sections = []
        # for section_id in course._section_ids:  # load every section
        #     # load all sections
        #     section_dict = self._get_request_api(
        #         "sections/{}".format(section_id), {})['sections'][0]
        #     unit_ids = section_dict['units']
        #
        #     lesson_list = []
        #
        #     for unit_id in unit_ids:
        #         lesson_id = units_dict[unit_id]['lesson']
        #         lesson_list.append(all_lessons_dict[lesson_id])
        #
        #     sections.append(Section(section_dict, lesson_list, self))

        return sections

    def get_step_by_lesson_id(self, lesson_id: int) -> List[Step]:
        lesson = self._impl._get_lesson(lesson_id)
        urls = self._impl._gen_urls("steps", lesson._steps_ids)
        step_dicts = self._impl._requests_url_async(urls, "steps")
        progresses = self._impl._gen_progresses_from_items(step_dicts)

        return [Step(step_dict, progress) for step_dict, progress in list(zip(
            step_dicts, progresses))]

    def get_step_text(self, step_id: int) -> str:
        step_dict = self._impl._get_request_api("steps/{}".format(step_id), {})
        return step_dict['steps'][0]['block']['text']

    def get_step_video(self, step_id: int) -> Video:
        step_dict = self._impl._get_request_api("steps/{}".format(step_id), {})
        return Video(step_dict['steps'][0]['block']['video'])

    def get_user_courses(self) -> List[Course]:
        courses_dicts = self._impl._get_content_from_all_pages(
            "courses", params={'enrolled': 'PWNED'})
        courses = []

        progresses = self._impl._gen_progresses_from_items(courses_dicts)

        for course_dict, progr in list(zip(courses_dicts, progresses)):
            courses.append(Course(course_dict, progr))
        return courses

    # this get raw data, but may be useful (or not)
    def _get_last_attempt_by_step_id(self, step_id: int) -> Optional[Attempt]:
        data = self._impl._get_request_api("attempts", {'step': str(step_id)})

        if len(data['attempts']) > 0:
            return Attempt(data['attempts'][0])
        else:
            return None

    def send_solution(self, step_id: int, data: str, params = "") \
    -> (str, str):
        import time
        step = self._impl._get_step_by_step_id(step_id)
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
        attempts = self._impl._get_request_api("attempts",
            {'step': str(step_id)})
        current_time = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
        if len(attempts['attempts']):
            attempt_id = attempts['attempts'][-1]['id']
        else:
            attempt = { 'attempt' : {
                "time": current_time,
                "step": step.id
            } }
            rs = requests.post('https://stepik.org:443/api/' + 'attempts',
                             headers={'Authorization': 'Bearer ' +
                                      self._impl.token},
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
                         headers={'Authorization': 'Bearer ' +
                                  self._impl.token},
                         json=submission).text
        nsubmission = json.loads(rs)['submissions'][0]
        submission_id = nsubmission['id']
        while nsubmission['status'] == 'evaluation':
            eta = nsubmission['eta']
            time.sleep(eta)
            nsubmission = self._impl._get_request_api(
                "submissions/" + str(submission_id),
                {})['submissions'][0]
        return (nsubmission['status'],
                nsubmission['hint'],
                nsubmission['feedback'])



class StepicClientImpl:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = self._get_token()
        self.API_URL_BASE = "https://stepik.org:443/api/"
        self._loop = asyncio.get_event_loop()

    def close(self):
        self._loop.run_until_complete(asyncio.sleep(0))
        self._loop.close()
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
    def _get_request_api(self, api_url_end: str, prms: dict) -> dict:
        data = json.loads(
            requests.get('https://stepik.org:443/api/' + api_url_end,
                         headers={'Authorization': 'Bearer ' + self.token},
                         params=prms
                         ).text
        )
        return data

    def _get_content_from_all_pages(self, api_name: str, params: dict) -> \
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

    # extract progress id from list of dictionaries
    def _extract_progress_ids(self, instances: List[dict]) -> List[int]:
        return [dct['progress'] for dct in instances]

    def _gen_progresses_from_items(self, item_dicts: List[dict]) -> \
            List[Progress]:
        progress_ids = self._extract_progress_ids(item_dicts)
        urls = self._gen_urls("progresses", progress_ids)
        progr_dicts = self._requests_url_async(urls, "progresses")
        return [Progress(progr_dict) for progr_dict in progr_dicts]

    ##########################################################################

    # steps information
    def _get_step_by_step_id(self, step_id: int) -> Step:
        step_data = self._get_request_api("steps/{}".format(step_id), {})
        step_dict = step_data['steps'][0]
        progress = self._get_progress_by_progress_id(step_dict['progress'])
        return Step(step_dict, progress)

    # return Course
    def _get_course_by_course_id(self, course_id: int) -> Course:
        data = self._get_request_api("courses/{}".format(course_id), {})
        course_dict = data['courses'][0]

        progress = self._get_progress_by_progress_id(course_dict['progress'])
        course = Course(course_dict, progress)
        return course

    def _get_lesson(self, lesson_id: int) -> Lesson:
        lesson_dict = self._get_request_api(
            "lessons/{}".format(lesson_id), {})['lessons'][0]
        progress_id = lesson_dict['progress']
        progress = self._get_progress_by_progress_id(progress_id)
        return Lesson(lesson_dict, progress)

    def _gen_urls(self, api_name, list_of_pks):
        return ["{}{}/{}".format(self.API_URL_BASE, api_name, pk)
                for pk in list_of_pks]

    # request list or urls
    def _requests_url_async(self, urls: List[str], key: str) -> List[dict]:
        async def get_json(loop, url):
            async with aiohttp.ClientSession(
                    loop=loop,
                    headers={'Authorization': 'Bearer ' + self.token}
            ) as client_session:
                async with client_session.get(url) as response:
                    return await response.read()

        loop_ = self._loop
        result_jsons = loop_.run_until_complete(
            asyncio.gather(
                *[get_json(loop_, url) for url in urls]
            )
        )

        dicts = []

        for json_str in result_jsons:
            dicts.append(json.loads(json_str)[key][0])

        return dicts

    ##### FUTURE #################################################
    def _get_last_attempt_by_step_id(self, step_id: int) -> Optional[Attempt]:
        data = self._get_request_api("attempts", {'step': str(step_id)})

        if len(data['attempts']) > 0:
            return Attempt(data['attempts'][0])
        else:
            return None

    # task info, NOT submissions here
    def _get_task_by_step_id(self, step_id: int) -> Optional[Task]:
        step = self._get_step_by_step_id(step_id)
        last_attempt = self._get_last_attempt_by_step_id(step_id)

        if last_attempt is not None:
            last_submission = self._get_last_submission_by_step_id(step_id)
            return Task(step, last_attempt, last_submission)
        return None

    # just for testing, not use it
    def _get_last_attempt_dict_by_step_id(self, step_id: int) -> Optional[
        Attempt]:
        data = self._get_request_api("attempts", {'step': str(step_id)})

        if len(data['attempts']) > 0:
            return data['attempts'][0]
        else:
            return None

    # def _get_all_attempt_by_step_id(self, step_id: int) -> List[Attempt]:
    #     data = self._get_request_api("attempts",
    #                                  {'step': str(step_id)})
    #
    #     if len(data['attempts']) > 0:
    #         return Attempt(data['attempts'][0])
    #     else:
    #         return None

    def _get_last_submission_by_step_id(self, step_id: int) \
            -> Optional[Submission]:
        data = self._get_request_api("submissions",
                                     {'step': str(step_id)})

        if len(data['attempts']) > 0:
            return Submission(data['submissions'][0])
        else:
            return None

    def _get_progress_by_progress_id(self, progress_id: str) -> \
            Optional[Progress]:
        if progress_id is not None:
            data = self._get_request_api("progresses/{}".format(progress_id),
                                         {})
            return Progress(data['progresses'][0])
        else:
            return None

