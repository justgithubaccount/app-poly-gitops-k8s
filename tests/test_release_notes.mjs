import fs from "node:fs";

import { analyzeCommits } from "@semantic-release/commit-analyzer";
import { generateNotes } from "@semantic-release/release-notes-generator";

const releaseConfig = JSON.parse(fs.readFileSync(".releaserc.json", "utf8"));
const analyzerPlugin = releaseConfig.plugins.find(
  (plugin) => Array.isArray(plugin) && plugin[0] === "@semantic-release/commit-analyzer",
);

if (!analyzerPlugin) {
  throw new Error("semantic-release commit analyzer configuration is missing");
}

const analyzerConfig = analyzerPlugin[1];
const logger = { log() {} };

const suppressedRelease = await analyzeCommits(
  analyzerConfig,
  {
    commits: [
      { message: "chore(no-release): clean configuration comments" },
      { message: "test(no-release): guard release suppression" },
      { message: "docs(no-release): modernize documentation" },
    ],
    logger,
  },
);

if (suppressedRelease !== null) {
  throw new Error(
    `no-release scope must suppress a release, received: ${suppressedRelease}`,
  );
}

const ordinaryChoreRelease = await analyzeCommits(
  analyzerConfig,
  {
    commits: [{ message: "chore: ordinary maintenance" }],
    logger,
  },
);

if (ordinaryChoreRelease !== "patch") {
  throw new Error(
    `ordinary chore must remain a patch release, received: ${ordinaryChoreRelease}`,
  );
}

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
