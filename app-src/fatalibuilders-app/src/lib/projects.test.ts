import { beforeEach, describe, expect, it } from "vitest";
import { resetDbForTests } from "@/db";
import { signup } from "./auth";
import { createProject, getProject, listProjects, updateProject } from "./projects";
import { projectDataSchema } from "./project-schema";

async function makeUser(email = "owner@example.com") {
  return signup(email, "password123");
}

const completeData = {
  codeProfile: "eurocode",
  country: "Kenya",
  floors: 1,
  footprintLengthM: 12,
  footprintWidthM: 9,
  floorHeightM: 2.8,
  wallType: "concrete_block",
  wallThicknessMm: 200,
  roofType: "gable_iron_sheets",
  doorsCount: 6,
  windowsCount: 8,
  plasterBothSides: true,
  paint: true,
  floorFinish: "screed",
  soilType: "black_cotton",
};

beforeEach(() => {
  resetDbForTests();
});

describe("project schema", () => {
  it("accepts a complete residential project and applies defaults", () => {
    const parsed = projectDataSchema.parse(completeData);
    expect(parsed.schemaVersion).toBe(1);
    expect(parsed.footprintLengthM).toBe(12);
  });

  it("coerces numeric strings from form inputs", () => {
    const parsed = projectDataSchema.parse({ ...completeData, footprintLengthM: "12.5" });
    expect(parsed.footprintLengthM).toBe(12.5);
  });

  it("rejects missing footprint and out-of-range values", () => {
    expect(projectDataSchema.safeParse({ ...completeData, footprintLengthM: undefined }).success).toBe(false);
    expect(projectDataSchema.safeParse({ ...completeData, floors: 9 }).success).toBe(false);
    expect(projectDataSchema.safeParse({ ...completeData, wallThicknessMm: 175 }).success).toBe(false);
  });
});

describe("project CRUD", () => {
  it("creates, lists and fetches a project for its owner", async () => {
    const user = await makeUser();
    const project = await createProject(user.id, "Villa in Kilifi");
    expect(project.status).toBe("draft");

    const list = await listProjects(user.id);
    expect(list.map((p) => p.id)).toContain(project.id);

    const fetched = await getProject(user.id, project.id);
    expect(fetched.name).toBe("Villa in Kilifi");
  });

  it("enforces ownership — another user gets 404", async () => {
    const alice = await makeUser("alice@example.com");
    const bob = await makeUser("bob@example.com");
    const project = await createProject(alice.id);
    await expect(getProject(bob.id, project.id)).rejects.toMatchObject({ status: 404 });
  });

  it("autosaves partial drafts and merges patches", async () => {
    const user = await makeUser();
    const project = await createProject(user.id);
    await updateProject(user.id, project.id, { data: { floors: 2 } });
    const updated = await updateProject(user.id, project.id, {
      data: { footprintLengthM: 10 },
    });
    expect(updated.data.floors).toBe(2); // earlier patch preserved
    expect(updated.data.footprintLengthM).toBe(10);
    expect(updated.status).toBe("draft");
  });

  it("refuses to complete an incomplete project, accepts a complete one", async () => {
    const user = await makeUser();
    const project = await createProject(user.id);
    await expect(
      updateProject(user.id, project.id, { status: "complete" }),
    ).rejects.toMatchObject({ status: 400 });

    const done = await updateProject(user.id, project.id, {
      data: completeData,
      status: "complete",
    });
    expect(done.status).toBe("complete");
    expect(done.data.schemaVersion).toBe(1);
  });

  it("rejects invalid draft patches with a clear error", async () => {
    const user = await makeUser();
    const project = await createProject(user.id);
    await expect(
      updateProject(user.id, project.id, { data: { floors: 99 } }),
    ).rejects.toMatchObject({ status: 400 });
  });

  it("404s on malformed project ids instead of crashing", async () => {
    const user = await makeUser();
    await expect(getProject(user.id, "not-a-uuid")).rejects.toMatchObject({ status: 404 });
  });
});
