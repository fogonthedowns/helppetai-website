- we need a function to book an appointment
- we have the pet owner id, after they verify
- a user's practice can be deterined this way: 
-postgres=> select id, pet_owner_id, practice_id from pet_owner_practice_associations;
                  id                  |             pet_owner_id             |             practice_id
--------------------------------------+--------------------------------------+--------------------------------------
 23e96f8f-cbb9-4d01-bf83-9bbd0788f5cb | 444cf6e3-4ee0-499e-9ced-d4e098fd1a21 | 934c57e7-4f9c-4d28-aa0f-3cb881e3c225

- we will get a local time, from thec customer, we need to write to UTC, I think we will have the time zone adjustement on practice
- I would LOVE to add appointment notes, with the concerns about the pet  - what's wrong with fido?