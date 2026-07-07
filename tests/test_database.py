from app.models import ReviewJob


def test_insert_job(session):

    job = ReviewJob(
        pr_url="https://github.com/demo/repo/pull/1"
    )

    session.add(job)
    session.commit()

    saved = session.get(ReviewJob, job.id)

    assert saved is not None
    assert saved.pr_url == job.pr_url


def test_update_job(session):

    job = ReviewJob(pr_url="abc")

    session.add(job)
    session.commit()

    job.status = "complete"

    session.add(job)
    session.commit()

    updated = session.get(ReviewJob, job.id)

    assert updated.status == "complete"