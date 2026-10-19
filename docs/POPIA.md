# POPIA checklist for Brights

Brights processes personal information of children (learners under 18), identity documents and
academic records. The code includes privacy protections (see SECURITY.md), but **software alone does
not make Brights compliant** with the Protection of Personal Information Act (POPIA).
The items below need legal and organisational work. Get advice from a South African privacy
lawyer before launch.

> This list was written by a developer, not a lawyer. Treat it as a starting point for that conversation.

## Organisational

- [ ] **Information Officer.** Phanda Technologies must have one (by default the head of the
      organisation) and register them with the Information Regulator.
- [ ] **Privacy policy** in plain language (learners will read it): what is collected, why, who
      sees it, how long it's kept, where it's stored, and how to ask for access or deletion.
- [ ] **Terms of use** for learners, parents and tutors, including the tutor code of conduct.
- [ ] **PAIA manual** (Promotion of Access to Information Act), usually required alongside POPIA.
- [ ] **Breach response plan.** Section 22 requires notifying the Regulator and affected people
      as soon as reasonably possible after a breach. Decide who does what.

## Children's information (sections 34–35)

- [ ] Brights currently records guardian consent with a **checkbox and the guardian's name**
      (the founder's decision in Phase 3). Ask whether this is adequate consent from a "competent
      person", or whether a stronger method (e.g. guardian email confirmation) is needed.
- [ ] Review the safety guidance shown to minors before contacting tutors, from a child-protection
      perspective.
- [ ] Decide whether parents should be notified when their child contacts a tutor.

## Identity documents and academic records

- [ ] Tutors upload ID copies and Matric results. Confirm the lawful basis and whether **prior
      authorisation** from the Information Regulator could apply (e.g. section 57, for processing unique
      identifiers for other purposes, or criminal-behaviour information if police clearance is ever added).
- [ ] **Retention:** decide how long verification documents are kept after a decision (e.g. delete
      ID copies a set time after approval or rejection) and build the deletion job. Not built yet.
- [ ] Decide which staff may view documents (only staff with the "Can view application document"
      permission can) and record that decision.

## Storing data outside South Africa (section 72)

The free pilot setup stores data with Render (Frankfurt), Neon (Frankfurt), Cloudflare R2 and Brevo.

- [ ] Confirm each provider offers adequate protection (e.g. EU GDPR coverage, data processing agreements).
- [ ] Mention cross-border storage in the privacy policy.
- [ ] Mention YouTube in the privacy policy: tutor how-to videos use YouTube's privacy-enhanced player,
      which only contacts Google when a tutor presses play.
- [ ] Consider moving to South African hosting before full launch (the code supports it; see DEPLOYMENT.md).

## Operators (section 21)

- [ ] Accept or sign the data processing terms of Render, Neon, Cloudflare and Brevo, and keep copies.

## Data subject rights (sections 23–25)

- [ ] **Access:** a way for users to request a copy of their data. Not built yet; can be manual by email at first.
- [ ] **Correction and deletion:** account deletion is not built yet. Review decisions and reports
      are kept as an audit trail (they can't be deleted), so deletion must **anonymise** personal details
      while keeping the record. Decide the rules, then build it.

## Retention schedule (to decide)

| Data | Suggested starting point to discuss |
|---|---|
| Verification documents | Delete a set period after the application decision |
| Contact log | Keep for a set period (e.g. 12 months) for safety investigations, then delete |
| Reports and review history | Keep longer (safety and legal reasons); anonymise when an account is deleted |
| Inactive accounts | Notify, then delete or anonymise after a set period of inactivity |

## Already in place (technical)

- Collect only what's needed. For example, guardian details are kept only for minor learners,
  street addresses are never collected, and photo GPS data is removed.
- Access control on every endpoint; private documents never publicly reachable.
- Encryption in transit (HTTPS, HSTS); secure cookies; rate limits; audit trails.
- Contact details revealed only through a logged, limited flow.
