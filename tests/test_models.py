from app.models import ReviewJob, ReviewReport


def test_create_review_job():

    job = ReviewJob(
        pr_url="https://github.com/test/repo/pull/1"
    )

    assert job.status == "pending"
    assert job.pr_url.endswith("/1")
    assert job.id is not None


def test_create_review_report():

    report = ReviewReport(
        job_id="123",
        pr_url="abc"
    )

    assert report.overall_score == 0
    assert report.summary == ""