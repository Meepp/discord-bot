from datetime import datetime

import pymongo
from bson import SON
from sqlalchemy import func

from database import mongodb as db
from src.database.models.models import Report


def add_report(report: Report):
    collection = db['report']
    try:
        collection.insert_one(report.to_mongodb())
        print("Added honor")
    except Exception as e:
        print(e)


# def get_all_reports(reportee):
#     collection = db['report']
#     print(reportee.id)
#     pipeline = [
#         {"$group": {"$_id": "$reportee", "count": {"$sum": 1}}},
#         {"match": {"$reportee_id": str(reportee.id)}},
#         {"$sort": SON([("count", -1), ("_id", -1)])}
#     ]
#     return list(collection.aggregate(pipeline))
    # return session.query(Report, func.count(Report.reporting_id)) \
    #     .filter(Report.guild_id == guild.id) \
    #     .filter(Report.reportee_id == reportee.id) \
    #     .group_by(Report.reporting_id) \
    #     .order_by(func.count(Report.reporting_id).desc()) \
    #     .all()


def get_reports():
    collection = db['report']
    pipeline = [
        {"$group": {"_id": "$reportee", "count": {"$sum": 1}}},
        {"$sort": SON([("count", -1), ("_id", -1)])}
    ]
    return list(collection.aggregate(pipeline))


def get_last_reports(guild, reporting):
    collection = db['report']

    return collection.find_one({"guild_id": guild.id, "reporting": reporting},
                               sort=[('_id', pymongo.DESCENDING)])


def report_allowed(guild, reporting):
    report = get_last_reports(guild, reporting.name)

    if report is None:
        return None

    diff = datetime.now() - report['time']
    if diff.total_seconds() // 60 < 30:
        return 30 - diff.seconds // 60
    else:
        return None
