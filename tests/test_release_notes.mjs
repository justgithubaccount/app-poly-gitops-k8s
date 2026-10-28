import { generateNotes } from "@semantic-release/release-notes-generator";

const notes = await generateNotes(
  {
    preset: "conventionalcommits",
    presetConfig: {
      types: [{ type: "fix", section: "Bug Fixes" }],
    },
  },
  {
    commits: [
      {
        hash: "0123456789abcdef",
        message: "fix: render release notes",
      },
    ],
    lastRelease: {
      gitHead: "0000000000000000",
      gitTag: "v0.0.0",
    },
    nextRelease: {
      gitHead: "0123456789abcdef",
      gitTag: "v1.0.0",
      version: "1.0.0",
    },
    options: {
      repositoryUrl: "https://github.com/justgithubaccount/app-poly-gitops-k8s.git",
    },
    cwd: process.cwd(),
  },
);

if (!notes.includes("render release notes")) {
  throw new Error(`generated notes did not include the commit subject:\n${notes}`);
}
