#!/usr/bin/env python3
import os
from datetime import datetime
from sty import fg
import sys
import argparse
from fuzzywuzzy import fuzz
import re
from stepik_to_markdown import stepik_to_markdown
from lib3 import StepicClient, CLIENT_ID, CLIENT_SECRET


# def lesson_type(s, pat=re.compile(r"\d+|first|last|next|prev")):
#     if not pat.match(s):
#         raise argparse.ArgumentTypeError
#     return s


def deadline_color(deadline: str, end='\n'):
    datetime_object = datetime.strptime(deadline, '%Y-%m-%dT%H:%M:%SZ')
    color_coef = (datetime_object - datetime.now()).total_seconds() / 3600.0 / 36
    if color_coef > 1:
        coloring_print(1, deadline, end=end)
    elif color_coef > 0:
        coloring_print(color_coef, deadline, end=end)
    else:
        coloring_print(0, deadline, end=end)


def step_type(s, pat=re.compile(r"\d+|first|last")):
    if not pat.match(s):
        raise argparse.ArgumentTypeError
    return s


def find_id_by_name(line: str, collection):
    maxi = 0
    id_max = -1
    for current in collection:
        new_maxi = max(maxi, fuzz.partial_ratio(line, current.title))
        if new_maxi != maxi:
            maxi = new_maxi
            id_max = current.id
    if maxi < 70:
        raise Exception('Bad pattern for search')

    return id_max

def isfloat(x):
    try:
        a = float(x)
    except ValueError:
        return False
    else:
        return True

def isint(x):
    try:
        a = float(x)
        b = int(a)
    except ValueError:
        return False
    else:
        return a == b


def coloring_progress(obj):
    if obj.progress is not None and int(obj.progress.cost) > 0:
        if isint(obj.progress.score):
            line = str(int(obj.progress.score)) + '/' + str(int(obj.progress.cost))
            coef = int(obj.progress.score) / int(obj.progress.cost)
        elif isfloat(obj.progress.score):
            line = str(float(obj.progress.score)) + '/' + str(int(obj.progress.cost))
            coef = float(obj.progress.score) / int(obj.progress.cost)
        else:
            raise Exception('Bad progress value')
        coloring_print(coef, line, end='\t')
    else:
        print('-/-', end='\t')

def coloring_print(i: float, line, end='\n'):
    fg.color = ('rgb', (int(255 * (1 - i)), int(255 * i), 0))
    buf = fg.color + str(line) + fg.rs
    print(buf, end=end)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Stepik cli.")

    parser.add_argument("--course", "-c", type=str, help='Search and return course id by name')
    parser.add_argument("--course-id", "-cid", dest='course_id', type=int, help='Return course id')

    parser.add_argument("--lesson", "-l", type=str, help='Return lesson id depending on it\'s index in course')
    parser.add_argument("--lesson-id", "-lid", dest='lesson_id', type=int, help='Return lesson id')

    parser.add_argument("--step", "-s", type=step_type, help='')
    parser.add_argument("--step-id", "-sid", dest='step_id', type=int, help='Return step id')

    args, unknown = parser.parse_known_args()
    out_variable = ''

    client = StepicClient(CLIENT_ID, CLIENT_SECRET)

    if args.course_id is not None:
        args.course = args.course_id
        out_variable = args.course
    elif args.course is None:
        try:
            args.course = int(os.environ['STEPIK_COURSE'])
            # out_variable = args.course
        except:
            pass
    else:
        try:
            args.course = find_id_by_name(args.course, client.get_user_courses())
            out_variable = args.course
        except:
            raise Exception('Error while searching course by name')

    if args.lesson_id is not None:
        args.lesson = args.lesson_id
        out_variable = args.lesson
    elif args.lesson is None:
        try:
            args.lesson = int(os.environ['STEPIK_LESSON'])
            # out_variable = args.lesson
        except:
            pass
            # raise Exception('Error in args.lesson: wrong env var STEPIK_LESSON')
    else:
        try:
            course_lessons_list = client.get_lessons_by_course_id(args.course)
            if args.lesson == 'first':
                args.lesson = course_lessons_list[0].id
                out_variable = args.lesson
            elif args.lesson == 'last':
                args.lesson = course_lessons_list[-1].id
                out_variable = args.lesson
            # elif args.lesson == 'next':
            #     try:
            #         cur_idx = -1
            #         for lsn in course_lessons_list:
            #             if lsn.id == os.environ['STEPIK_LESSON']:
            #                 cur_idx = course_lessons_list.index(lsn)
            #         if cur_idx > -1:
            #             try:
            #                 args.lesson = course_lessons_list[cur_idx + 1].id
            #                 out_variable = args.lesson
            #             except:
            #                 raise Exception('Error in args.lesson: error while next command')
            #         else:
            #             raise Exception('Error in args.lesson: env lesson id absent in course')
            #     except:
            #         raise Exception('Error in args.lesson part next')
            # elif args.lesson == 'prev':
            #     try:
            #         cur_idx = -1
            #         for lsn in course_lessons_list:
            #             if lsn.id == int(os.environ['STEPIK_LESSON']):
            #                 cur_idx = course_lessons_list.index(lsn)
            #         if cur_idx > -1:
            #             try:
            #                 args.lesson = course_lessons_list[cur_idx - 1].id
            #                 out_variable = args.lesson
            #             except:
            #                 raise Exception('Error in args.lesson: error while prev command')
            #         else:
            #             raise Exception('Error in args.lesson: env lesson id absent in course')
            #     except:
            #         raise Exception('Error in args.lesson part next')
            elif args.lesson.isdigit():  # part index
                try:
                    args.lesson = course_lessons_list[int(args.lesson) - 1].id
                    out_variable = args.lesson
                except:
                    raise Exception('Error in args.lesson part next')
            else:
                try:
                    args.lesson = find_id_by_name(args.lesson, course_lessons_list)
                    out_variable = args.lesson
                except:
                    raise Exception('Error while searching course by name')
        except:
            raise Exception('Error in args.lesson: bad getting lessons by course id')

    if args.step_id is not None:
        args.step = args.step_id
        out_variable = args.step
    elif args.step is None:
        try:
            args.step = int(os.environ['STEPIK_STEP'])
            # out_variable = args.step
        except:
            pass
            # raise Exception('Error in args.step: wrong env var STEPIK_STEP')
    else:
        step_list = client.get_step_by_lesson_id(args.lesson)
        if args.step == 'first':
            args.step = step_list[0].id
            out_variable = args.step
        elif args.step == 'last':
            args.step = step_list[-1].id
            out_variable = args.step
        # elif args.step == 'next':
        #     try:
        #         cur_idx = -1
        #         for stp in step_list:
        #             if stp.id == int(os.environ['STEPIK_STEP']):
        #                 cur_idx = step_list.index(stp)
        #         if cur_idx > -1:
        #             try:
        #                 args.step = step_list[cur_idx + 1].id
        #                 out_variable = args.step
        #             except:
        #                 raise Exception('Error in args.step: error while next command')
        #         else:
        #             raise Exception('Error in args.step: env step id absent in lesson')
        #     except:
        #         raise Exception('Error in args.step part next')
        # elif args.step == 'prev':
        #     try:
        #         cur_idx = -1
        #         for stp in step_list:
        #             if stp.id == int(os.environ['STEPIK_STEP']):
        #                 cur_idx = step_list.index(stp)
        #         if cur_idx > -1:
        #             try:
        #                 args.step = step_list[cur_idx - 1].id
        #                 out_variable = args.step
        #             except:
        #                 raise Exception('Error in args.step: error while prev command')
        #         else:
        #             raise Exception('Error in args.step: env step id absent in lesson')
        #     except:
        #         raise Exception('Error in args.step part prev')

        # elif args.step == 'unsolved':
        #     pass #TODO итерируемся по степам от начала и проверяем процент заполненности
        else:  # part index
            try:
                args.step = step_list[int(args.step) - 1].id
                out_variable = args.step
            except:
                raise Exception('Error in args.step part index')

    if unknown:
        if unknown[0] == 'courses':
            try:
                user_courses_list = client.get_user_courses()
                for i, user_course in enumerate(user_courses_list, start=1):
                    print('{}\t{}\t{}\t'.format(i, user_course.id, user_course.title), end='\t')
                    coloring_progress(user_course)
                    print()

            except:
                raise Exception('Error in courses: can\'t get user courses')
            # finally:
            #     exit()

        elif unknown[0] == 'lessons':
            try:
                course_sections_list = client.get_sections(args.course)
                for i, section in enumerate(course_sections_list, start=1):
                    print(i, section.title, sep='\t', end='\t')
                    # TODO раскрасить дедлайны
                    coloring_progress(section)

                    if section.soft_deadline is not None:
                        deadline_color(section.soft_deadline, end='\t')
                    else:
                        print('-', end='\t')

                    if section.hard_deadline is not None:
                        deadline_color(section.hard_deadline, end='\n')
                    else:
                        print('-', end='\n')


                    for j, les in enumerate(section.lesson_list, start=1):
                        print('{}.{}\t{}\t{}'.format(i, j, les.id, les.title), end='\t')
                        coloring_progress(les)
                        print()

            except:
                raise Exception('Error in args.lesson: no course_id')
            # finally:
            #     exit()

        elif unknown[0] == 'steps':
            try:
                lesson_steps_list = client.get_step_by_lesson_id(args.lesson)
                for i, step in enumerate(lesson_steps_list, start=1):
                    print(i, step.id, step.type, sep='\t', end='\t')
                    # coloring_progress(step)
                    print()

            except:
                raise Exception('Error in arg steps')
            # finally:
            #     exit()

        elif unknown[0] == 'text':
            print(stepik_to_markdown(client.get_step_text(args.step)))
        # elif unknown[0] == 'languages':
        #     print(client._get_step_by_step_id(args.step).code_options)

        elif unknown[0] == 'template':
            try:
                arg = unknown[1]

            except:
                raise Exception('Bad language template')

        elif unknown[0] == 'video':
            urls_dict = client.get_step_video(args.step).urls
            maxi = 0
            for key in urls_dict.keys():
                maxi = max(maxi, int(key))
            print(urls_dict.get(str(maxi)))

        elif unknown[0] == 'send':
            data = sys.stdin.read().strip()
            if len(unknown) > 1:
                result, hint, answer = client.send_solution(args.step, data, unknown[1])
            else:
                result, hint, answer = client.send_solution(args.step, data)

            if result == 'wrong':
                color = 0
            else:
                color = 1

            if hint != '':
                coloring_print(color, result, end=': ')
                print(hint)
            elif hint == answer:
                coloring_print(color, result, end='\n')
            print(answer)

        elif unknown[0] == 'task':
            pass
        else:
            raise Exception('Unknown command')
    else:
        print(out_variable)
