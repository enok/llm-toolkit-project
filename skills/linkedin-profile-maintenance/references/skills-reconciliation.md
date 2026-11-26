# Skills reconciliation

How to bring the LinkedIn Skills section in line with a target plan without
losing endorsements or hitting the cap by surprise.

## 1. Inventory

- Scroll the skills details page to the footer (the list loads lazily) and
  extract the text; record name and associations per skill.
- Endorsement counts appear in each skill's detail dialog. A skill with
  endorsements costs something to remove or rename; a skill with none is free.
- Compute the final count before touching anything:
  `final = current - removals + additions`. The cap is 100. If `final > 100`,
  propose cuts to the owner first (overlapping or legacy skills with no
  endorsements), then start.

## 2. Plan table (owner-approved)

| Action | Meaning |
| --- | --- |
| Add | New skill, with the roles/education it should be linked to |
| Link | Existing skill, add an association (usually the current role) |
| Replace | Add the better-named skill, re-link the old skill's roles, delete the old one |
| Remove | Delete after confirming no endorsements the owner cares about |
| Pin | Top five shown on the profile; chosen last |

Rows to expect after a career change: the current role has few associations;
add it to the long-standing skills (language, framework, database, container,
VCS, OS, methodology) in addition to the new ones.

## 3. What the platform does (observed)

- **Variants are one record.** Adding "Gitlab" when "GitLab" exists, or "Postman"
  when "Postman API" exists, returns "This skill is already on your profile".
  The planned replacement is a no-op and endorsements are preserved. Do not try
  to delete and re-add.
- **Standardized names differ from the name you want.** The typeahead offers a
  fixed vocabulary ("Software Development", not "Software Engineering"; "Systems
  Design", not "System Design"; "Amazon OpenSearch", not "OpenSearch"). Accept the
  closest same-meaning option when the owner has allowed it, and list every
  substitution at the end.
- **Some names do not exist** (for example a plain "Observability" may be missing
  while a longer variant exists). Keep the existing near-equivalent and report it.
- **A skill that is already absent** from the section can still appear inside old
  role descriptions as text; that is a text edit, not a skills action.
- **At the cap, adds fail.** Delete the least valuable no-endorsement skill first.

## 4. Add flow

1. Open `/in/<handle>/skills/edit/forms/new/` (the Add skill dialog).
2. Type the name, wait for suggestions, click the matching option (typing alone
   does not select it).
3. Tick every role/education it should be linked to (find the checkboxes by label;
   refs repeat per skill on the same form).
4. Save; wait for the confirmation toast; navigate to the form URL again for the
   next skill (references reset after each save).

## 5. Link an existing skill

Open `/in/<handle>/details/skills/edit/forms/<skillId>/` (skill ids are in the
edit links on the skills details page), tick the role checkbox, Save, and read
the association back from the details page.

## 6. Delete flow

Edit dialog -> "Delete skill" -> confirm "Delete". Do it only after the
replacement exists and is linked. A confirmation dialog states that the action
cannot be undone.

## 7. Pin the top five

Pins live in the About edit dialog, in its Skills block (max five, order = display
order). Remove the current pins with their X buttons, then use "Add skill" and
pick the option listed under "Currently in your Skills section" for each. Save
the About dialog. If the About text is also changing, edit the text in the same
dialog and save once.

## 8. Final check

Re-open the skills page, scroll to the footer, count entries, and confirm the
top-five line on the profile card. Report the numbers.
