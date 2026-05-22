from server.app.quiz.services.category_seed_service import seed_all_category_quizzes


async def seed_all():
    stats = await seed_all_category_quizzes()
    print(
        "Category seed sync completed: "
        f"{stats['created']} created, "
        f"{stats['updated']} updated, "
        f"{stats['unchanged']} unchanged, "
        f"{stats['skipped']} skipped, "
        f"{stats['errors']} errors."
    )
    return stats


if __name__ == "__main__":
    import asyncio

    print("Seeding categorized quiz banks into quizzes_v2...")
    asyncio.run(seed_all())
    print("Done seeding categorized quizzes.")
