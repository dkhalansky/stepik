'''
    Wrapper around stepic API
'''
import json
import sys
import traceback
from typing import List

import requests
import requests.auth

# STEPIC_URL = "https://stepic.org/api"
# APP_FOLDER = ".stepic"
# CLIENT_FILE = APP_FOLDER + "/client_file"
# ATTEMPT_FILE = APP_FOLDER + "/attempt_file"

CLIENT_ID = "eByNx7sclqIzXfdn6Teinowor5vh4ObcwIvquD3b"
CLIENT_SECRET = "9aMC6hPALE4zCHCaw9s3TGMkrCBK5byIITInmXOjFMpb7Sv58jtEFBLJ9c3C6joIP9c0lOtYNT5sDzuhNedr15Zdfwpr2dXUOKB9FiaWC87xiMus1bvUUAdV72tlaW13"


class Course:
    def __init__(self, decoded_data: dict):
        self.id = decoded_data['id']
        self.title = decoded_data['title']

        self._section_ids = decoded_data['sections']
        # todo grab more data


class Lesson:
    def __init__(self, decoded_data: dict):
        self.id = decoded_data['id']
        self.title = decoded_data['title']

        self._steps_ids = decoded_data['steps']
        # todo grab more data


class Section:
    def __init__(self, decoded_data: dict, lesson_list: List[Lesson]):
        self.id = decoded_data['id']
        self.title = decoded_data['title']
        self.hard_deadline = decoded_data['hard_deadline']
        self.soft_deadline = decoded_data['soft_deadline']

        self.lesson_list = lesson_list
        # todo grab more data


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
    def __init__(self, steps_data: dict):
        self.id = steps_data['id']
        self.lesson = steps_data['lesson']
        self._block = Block(steps_data['block'])  # from api

        self.type = self._block.name  # str, 'video' or others
        self.video = self._block.video
        self.text = self._block.text
        # todo grab more data


class Attempt:
    def __init__(self, steps_data: dict):
        self.id = steps_data['id']
        self.dataset = steps_data['dataset']  # dict with task data
        self.dataset_url = steps_data['dataset_url']
        self.step = steps_data['step']
        self.user = steps_data['user']
        # todo parse dataset, it can be different


class StepicClient:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = self._get_token()

    def _get_token(self):
        auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
        resp = requests.post('https://stepik.org/oauth2/token/',
                             data={
                                 'grant_type': 'client_credentials',
                             },
                             auth=auth)
        token = json.loads(resp.text)['access_token']
        return token

    def _get_wrapper(self, api_url: str, prms: dict, token: str) -> dict:
        data = json.loads(
            requests.get(api_url,
                         headers={'Authorization': 'Bearer ' + token},
                         params=prms
                         ).text
        )
        return data

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

    # get_wrapper: pageNum -> token -> dict()
    # content_extractor:
    def _get_content_from_all_pages(self, token: str, get_wrapper,
                                    content_extractor, Constructor):
        pageNum = 0
        hasNextPage = True
        accumulator_list = []

        try:
            while hasNextPage:
                pageNum += 1
                pageContent = get_wrapper(pageNum, token)
                hasNextPage = pageContent['meta']['has_next']
                contents = content_extractor(pageContent)

                for content in contents:
                    accumulator_list.append(Constructor(content))

            return accumulator_list

        except Exception:
            traceback.print_exc(file=sys.stdout)
            print("Error exception: something was broken!")

    #############################################################################
    # return [Section]
    def _get_sections_by_course_id(self, course_id: int) -> List[Section]:
        course = self._get_course_by_course_id(course_id)

        sections = []
        for sect_id in course._section_ids:
            sec_data = self._get_request_api(
                "sections/{}".format(sect_id), {})
            sections.append(Section(sec_data['sections'][0], None))

        return sections

    # return  [Lesson]
    def get_lessons_by_course_id(self, course_id: int) -> List[Lesson]:
        def loader(page_num, token):
            api_url = 'https://stepik.org/api/lessons'
            params = {
                'page': str(page_num),
                'course': str(course_id)
            }
            return self._get_wrapper(api_url, params, token)

        def extractor(json_data):
            return json_data['lessons']

        return self._get_content_from_all_pages(self.token, loader,
                                                extractor, Constructor=Lesson)

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
        course = Course(data['courses'][0])
        return course

    def _get_lesson(self, lesson_id: int) -> Lesson:
        lesson_dict = self._get_request_api(
            "lessons/{}".format(lesson_id), {})['lessons'][0]
        return Lesson(lesson_dict)

    ##############################################################################
    # return [Course]
    def get_user_courses(self) -> List[Course]:
        def loader(page_num, token):
            api_url = 'https://stepik.org/api/courses'
            params = {
                'page': str(page_num),
                'enrolled': 'PWNED'
            }
            return self._get_wrapper(api_url, params, token)

        def extractor(json_data):
            return json_data['courses']

        return self._get_content_from_all_pages(self.token, loader, extractor,
                                                Constructor=Course)

    # SO SLOW
    def get_sections(self, course_id: int) -> List[Section]:
        course = self._get_course_by_course_id(course_id)

        all_lessons = self.get_lessons_by_course_id(course_id)
        lesson_ix = 0

        sections = []
        for section_id in course._section_ids:
            section_dict = self._get_request_api(
                "sections/{}".format(section_id), {})['sections'][0]

            lesson_list = []
            unit_ids = section_dict['units']
            for unit_id in unit_ids:
                # unit has lessons
                # unit_dict = self._get_request_api(
                #     "units/{}".format(unit_id), {})['units'][0]
                # lesson = self._get_lesson(unit_dict['lesson'])

                lesson_list.append(all_lessons[lesson_ix])
                lesson_ix += 1

            sections.append(Section(section_dict, lesson_list))
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
                'language': param,
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

    ##### FUTURE #################################################
    # task info, NOT submissions here
    def get_attempts_by_step_id(self, step_id: int):
        data = self._get_request_api("attempts",
                                     {'step': str(step_id)})
        attempts = []

        for attemp_data in data['attempts']:
            attempts.append(Attempt(attemp_data))

        return attempts


def main():
    client = StepicClient(CLIENT_ID, CLIENT_SECRET)
    client.send_solution(211735, "4 7 11")
    # elems = client.get_user_courses()
    # for elem in elems:
    #     print("## Id = {} with title: '{}'".format(
    #         elem.id, elem.title))

    # # printing all lessons
    # elems = client.get_lessons_by_course_id(125)
    # for elem in elems:
    #     print("## Id = {} with title: '{}'".format(
    #         elem.id, elem.title))

    # # example of getting video url
    # step = client.get_steps(170472)
    # print(step.block.video.urls['360'])

    # # example of printing section names for course
    # sections = client.get_sections_by_course_id(125)
    # for sec in sections:
    #     print(sec.title)

    # attempts = client.get_attempts_by_step_id(170499)
    # for att in attempts:
    #     print(att.id)

    # data = client._get_request_api(client.token, "attempts",
    #                                {'step': str(170499)})
    # print(data)

    # sections = client.get_sections(125)
    # for sect in sections:
    #     print("## Id = {} with title: '{}'".format(
    #         sect.id, sect.title))
    #     for lesson in sect.lesson_list:
    #         print("## \t lesson: {}".format(lesson.title))


if __name__ == '__main__':
    main()

