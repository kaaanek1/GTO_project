from db import get_optional_categories, get_required_categories, get_all_entries
from kivy.storage.jsonstore import JsonStore
import sqlite3


def get_badge_for_result(result, gold, silver, bronze, unit):
    """Определяет полученный знак для результата с учетом типа упражнения"""
    # Для упражнений, где меньшее значение лучше (время, секунды)
    if unit in ['сек', 'с']:
        if result <= gold:
            return 'gold'
        elif result <= silver:
            return 'silver'
        elif result <= bronze:
            return 'bronze'
    # Для упражнений, где большее значение лучше (метры, количество раз и т.д.)
    else:
        if result >= gold:
            return 'gold'
        elif result >= silver:
            return 'silver'
        elif result >= bronze:
            return 'bronze'
    return None


def is_better_result(exercise, stage, gender, new_result, old_result):
    """Определяет, является ли новый результат лучше старого для данного упражнения"""
    conn = sqlite3.connect('gto.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT unit FROM standards 
    WHERE exercise = ? AND stage = ? AND gender = ?
    ''', (exercise, stage, gender))
    unit = cursor.fetchone()[0]
    conn.close()

    # Для упражнений, где меньшее значение лучше (время, секунды)
    if unit in ['сек', 'с']:
        return new_result < old_result
    # Для упражнений, где большее значение лучше (метры, количество раз и т.д.)
    else:
        return new_result > old_result


def calculate_badge(user_data):
    """Рассчитывает, какой знак ГТО может получить пользователь"""
    # Уровни знаков для сравнения
    badge_levels = {'gold': 3, 'silver': 2, 'bronze': 1}

    store = JsonStore('user_data.json')
    if not store.exists('user'):
        return None

    user_data = store.get('user')
    stage = user_data['stage']
    gender = user_data['gender']

    # Получаем все записи пользователя
    all_entries = get_all_entries()

    # Группируем записи по упражнениям (берем только лучший результат для каждого)
    exercise_results = {}
    for entry in all_entries:
        exercise = entry['exercise']
        try:
            result = float(entry['result'])
            if exercise not in exercise_results or is_better_result(exercise, stage, gender, result,
                                                                    exercise_results[exercise]['result']):
                exercise_results[exercise] = {
                    'result': result,
                    'entry': entry
                }
        except ValueError:
            continue

    # Получаем обязательные категории и категории по выбору
    required_categories = get_required_categories(stage, gender)
    optional_categories = get_optional_categories(stage, gender)

    # Проверяем выполненные обязательные нормативы
    completed_required = []
    missing_required = []

    for category in required_categories:
        # Находим все упражнения в этой категории
        conn = sqlite3.connect('gto.db')
        cursor = conn.cursor()
        cursor.execute('''
        SELECT exercise FROM standards 
        WHERE stage = ? AND gender = ? AND category = ? AND type = 1
        ''', (stage, gender, category))
        exercises_in_category = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Ищем лучшее выполненное упражнение в категории
        best_in_category = None

        for exercise in exercises_in_category:
            if exercise in exercise_results:
                # Получаем норматив для этого упражнения
                conn = sqlite3.connect('gto.db')
                cursor = conn.cursor()
                cursor.execute('''
                SELECT gold, silver, bronze, unit FROM standards 
                WHERE exercise = ? AND stage = ? AND gender = ?
                ''', (exercise, stage, gender))
                standards = cursor.fetchone()
                conn.close()

                if standards:
                    gold, silver, bronze, unit = standards
                    result = exercise_results[exercise]['result']

                    # Определяем знак для этого результата
                    badge = get_badge_for_result(result, gold, silver, bronze, unit)

                    if badge:
                        if not best_in_category or badge_levels[badge] > badge_levels[best_in_category['badge']]:
                            best_in_category = {
                                'exercise': exercise,
                                'result': result,
                                'badge': badge,
                                'gold': gold,
                                'silver': silver,
                                'bronze': bronze,
                                'unit': unit
                            }

        if best_in_category:
            completed_required.append(best_in_category)
        else:
            missing_required.append(category)

    # Проверяем выполненные нормативы по выбору
    completed_optional = []
    for category in optional_categories:
        # Находим все упражнения в этой категории
        conn = sqlite3.connect('gto.db')
        cursor = conn.cursor()
        cursor.execute('''
        SELECT exercise FROM standards 
        WHERE stage = ? AND gender = ? AND category = ? AND type = 0
        ''', (stage, gender, category))
        exercises_in_category = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Ищем лучшее выполненное упражнение в категории
        best_in_category = None

        for exercise in exercises_in_category:
            if exercise in exercise_results:
                # Получаем норматив для этого упражнения
                conn = sqlite3.connect('gto.db')
                cursor = conn.cursor()
                cursor.execute('''
                SELECT gold, silver, bronze, unit FROM standards 
                WHERE exercise = ? AND stage = ? AND gender = ?
                ''', (exercise, stage, gender))
                standards = cursor.fetchone()
                conn.close()

                if standards:
                    gold, silver, bronze, unit = standards
                    result = exercise_results[exercise]['result']

                    # Определяем знак для этого результата
                    badge = get_badge_for_result(result, gold, silver, bronze, unit)

                    if badge:
                        if not best_in_category or badge_levels[badge] > badge_levels[best_in_category['badge']]:
                            best_in_category = {
                                'exercise': exercise,
                                'result': result,
                                'badge': badge,
                                'gold': gold,
                                'silver': silver,
                                'bronze': bronze,
                                'unit': unit
                            }

        if best_in_category:
            completed_optional.append(best_in_category)

    # Определяем минимальный знак среди выполненных нормативов
    min_badge = 'gold'
    for item in completed_required:
        if badge_levels[item['badge']] < badge_levels[min_badge]:
            min_badge = item['badge']

    # Определяем итоговый результат
    result = {
        'can_get_badge': False,
        'badge': None,
        'missing_required': missing_required,
        'missing_optional': 0,
        'completed_required': completed_required,
        'completed_optional': completed_optional
    }

    # Если есть несданные обязательные нормативы → знак не получить
    if missing_required:
        return result

    # Если нет ни одного норматива по выбору → знак не получить
    if not completed_optional:
        result['missing_optional'] = 1  # нужно сдать минимум 1
        return result

    # Определяем, сколько нормативов по выбору нужно для текущего min_badge
    required_optional = 2 if min_badge == 'gold' else 1

    if len(completed_optional) >= required_optional:
        result['can_get_badge'] = True
        result['badge'] = min_badge
    else:
        result['missing_optional'] = required_optional - len(completed_optional)

    return result