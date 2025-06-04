import sqlite3
from typing import List, Dict


def get_standards_for_stage(stage: int, gender: str) -> List[Dict]:
    conn = sqlite3.connect("gto.db")
    cursor = conn.cursor()

    query = """
    SELECT exercise, gold, silver, bronze, unit 
    FROM standards 
    WHERE stage = ? AND gender = ?
    ORDER BY exercise
    """
    cursor.execute(query, (stage, gender))
    standards = cursor.fetchall()
    conn.close()


    return [
        {
            "exercise": row[0],
            "gold": row[1],
            "silver": row[2],
            "bronze": row[3],
            "unit": row[4]
        }
        for row in standards
    ]


def get_stage_info(stage: int) -> Dict:
    """Возвращает информацию о ступени (возрастной диапазон)"""
    stages = {
        1: "6-7 лет",
        2: "8-9 лет",
        3: "10-11 лет",
        4: "12-13 лет",
        5: "14-15 лет",
        6: "16-17 лет",
        7: "18-19 лет",
        8: "20-24 года",
        9: "25-29 лет",
        10: "30-34 года",
        11: "35-39 лет",
        12: "40-44 года",
        13: "45-49 лет",
        14: "50-54 года",
        15: "55-59 лет",
        16: "60-64 года",
        17: "65-69 лет",
        18: "70+ лет"
    }
    return {
        "number": stage,
        "age_range": stages.get(stage)
    }