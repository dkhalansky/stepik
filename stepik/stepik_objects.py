'''
Some class for representation data types we get from stepik throug api.
'''
from typing import List


class Progress:
    def __init__(self, data: dict):
        # print(data)
        self.id = data['id']
        self.score = data['score']
        self.cost = data['cost']
        self.n_steps = data['n_steps']
        self.n_steps_passed = data['n_steps_passed']
        self.is_passed = data['is_passed']


class Video:
    def __init__(self, video_dict: dict):
        self.id = video_dict['id']
        self.thumbnail = video_dict['thumbnail']
        self.urls = {}
        for dct in video_dict['urls']:
            self.urls[dct['quality']] = dct['url']


class Block:
    def __init__(self, block_dict: dict):
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
    def __init__(self, steps_data: dict, progress: Progress):
        self.id = steps_data['id']
        self.lesson = steps_data['lesson']
        self._block = Block(steps_data['block'])  # from api

        self.type = self._block.name  # str, 'video' or others
        self.code_options = self._block.options if self.type == "code" else \
            None
        self.video = self._block.video
        self.text = self._block.text

        self._progress_id = steps_data['progress']
        self.progress = progress


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
                 progr: Progress):
        self.id = decoded_data['id']
        self.title = decoded_data['title']
        self.hard_deadline = decoded_data['hard_deadline']
        self.soft_deadline = decoded_data['soft_deadline']

        self.lesson_list = lesson_list

        # todo SCORE FOR IT
        self._progress_id = decoded_data['progress']
        self.progress = progr


class Course:
    def __init__(self, decoded_data: dict, progr: Progress):
        self.id = decoded_data['id']
        self.title = decoded_data['title']
        self._section_ids = decoded_data['sections']

        self._progress_id = decoded_data['progress']
        self.progress = progr
        # todo SCORE FOR IT
        # todo grab more data


class Attempt:
    def __init__(self, type: str, steps_data: dict):
        self.type = type
        self.id = steps_data['id']
        self.dataset = steps_data['dataset']  # dict with task data
        self.dataset_url = steps_data['dataset_url']
        self.step_id = steps_data['step']
        self.user_id = steps_data['user']
        self.time = steps_data['time']
        # todo parse dataset, it can be different


# not used, but may be
class Submission:
    def __init__(self, data: dict):
        self.id = data['id']  # :: int
        self.status = data['status']  # :: str
        self.score = data['score']  # :: int
        self.reply = data['reply']  # :: dict
        self.attempt_id = data['attempt']
        self.time = data['time']


# unused
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
        # todo do all fucking stuff
        pass
        # self.type
        # self.step_text
        # self.
