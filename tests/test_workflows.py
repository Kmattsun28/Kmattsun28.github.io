import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class ContentWorkflowTests(unittest.TestCase):
    def test_content_workflows_do_not_require_unconfigured_secret(self):
        for workflow_name in ("add-activity.yml", "add-publication.yml"):
            workflow = (REPO_ROOT / ".github" / "workflows" / workflow_name).read_text(
                encoding="utf-8"
            )
            self.assertNotIn("SITE_UPDATE_TOKEN", workflow)

    def test_content_workflows_trigger_deploy_after_success(self):
        deploy = (REPO_ROOT / ".github" / "workflows" / "deploy.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("workflow_run:", deploy)
        self.assertIn("Add activity", deploy)
        self.assertIn("Add publication", deploy)

    def test_toc_workflow_formats_markdown_after_updating_toc(self):
        update_tocs = (REPO_ROOT / ".github" / "workflows" / "update-tocs.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("npm ci --ignore-scripts", update_tocs)
        self.assertIn("npx prettier", update_tocs)

    def test_activity_list_uses_slice_for_homepage_limit(self):
        activities_list = (REPO_ROOT / "_includes" / "activities_list.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("| slice: 0, include.limit", activities_list)
        self.assertNotIn("| limit: include.limit", activities_list)


if __name__ == "__main__":
    unittest.main()
