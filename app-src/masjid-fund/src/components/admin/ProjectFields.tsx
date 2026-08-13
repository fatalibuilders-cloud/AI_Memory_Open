import type { Project } from "@/lib/projects";

/**
 * The project form body, shared by the create and edit screens. Money is typed
 * in whole currency units and converted to cents server-side.
 */
export function ProjectFields({ project }: { project?: Project }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Field label="Name" name="name" defaultValue={project?.name} required />
      <Field
        label="Slug"
        name="slug"
        defaultValue={project?.slug}
        hint="Used in the URL: /projects/your-slug"
        required
      />
      <Field label="City" name="city" defaultValue={project?.city} required />
      <Field label="Country" name="country" defaultValue={project?.country} required />

      <div className="sm:col-span-2">
        <Field
          label="Summary"
          name="summary"
          defaultValue={project?.summary}
          hint="One sentence, shown on the project card"
          required
        />
      </div>

      <label className="sm:col-span-2 block">
        <span className="text-sm font-medium">Story</span>
        <textarea
          name="story"
          rows={6}
          required
          defaultValue={project?.story}
          className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
        />
        <span className="mt-1 block text-xs text-sand-700">
          What the community has now, what is being built, who owns the land.
        </span>
      </label>

      <label className="block">
        <span className="text-sm font-medium">Status</span>
        <select
          name="status"
          defaultValue={project?.status ?? "planning"}
          className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
        >
          <option value="planning">Preparing to build</option>
          <option value="building">Under construction</option>
          <option value="completed">Completed</option>
        </select>
      </label>

      <label className="block">
        <span className="text-sm font-medium">Card artwork</span>
        <select
          name="accent"
          defaultValue={project?.accent ?? "emerald"}
          className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
        >
          <option value="emerald">Emerald</option>
          <option value="teal">Teal</option>
          <option value="sky">Sky</option>
          <option value="amber">Amber</option>
        </select>
      </label>

      <Field
        label="Total budget"
        name="goal"
        defaultValue={project ? String(project.goalCents / 100) : ""}
        hint="Whole currency units, e.g. 85000"
        required
      />
      <Field
        label="Raised offline"
        name="offlineRaised"
        defaultValue={project ? String(project.offlineRaisedCents / 100) : "0"}
        hint="Historic total carried in from outside the site"
      />
      <Field
        label="Capacity"
        name="capacity"
        defaultValue={project ? String(project.capacity) : "0"}
        hint="Worshippers"
      />
      <Field
        label="Sort order"
        name="position"
        defaultValue={project ? String(project.position) : "0"}
        hint="Lower numbers list first"
      />
    </div>
  );
}

function Field({
  label,
  name,
  defaultValue,
  hint,
  required,
}: {
  label: string;
  name: string;
  defaultValue?: string;
  hint?: string;
  required?: boolean;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium">{label}</span>
      <input
        name={name}
        defaultValue={defaultValue}
        required={required}
        className="mt-1 w-full rounded-xl border border-sand-200 bg-white px-3 py-3 outline-none focus:ring-2 focus:ring-masjid-500"
      />
      {hint && <span className="mt-1 block text-xs text-sand-700">{hint}</span>}
    </label>
  );
}
