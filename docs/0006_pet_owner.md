Pet Owner - REST API & Frontend
Backend Requirements
REST Endpoints

Role Options (for reference) PetOwner, Admin, Vet

GET /api/v1/pet_owners - List all pet owners (Admin only | no other role has access)
GET /api/v1/pet_owners/{uuid} - View single pet owner (Admin | Current User logged in must be that uuid)
POST /api/v1/pet_owners - Create pet owner (User must be logged in - no role needed)
PUT /api/v1/pet_owners/{uuid} - Update pet owner (Admin | Current User logged in must be that uuid |no other role has access)
DELETE /api/v1/pet_owners/{uuid} - Delete pet owner (admin only | no other role has access)

Technical Specs

Use UUID primary keys (not numerical IDs)
No Public access for CRUD operations

Frontend Requirements
Pages/Components

Pet Owner list page (admin)
Pet Owner detail page (object owner | admin)
Pet Owner create/edit form (admin only. no acesss to patients, vets, etc)
Admin pet owner management dashboard

Design

Follow existing /vets endpoint UI patterns
Responsive React components
Role-based component rendering (hide admin features for non-admins)

Acceptance Criteria

 All REST endpoints implemented with proper HTTP methods
 UUID-based routing works correctly
 Public must be logged in to create pet owner
 Update must be the pet owner, corresponding to the uuid that is logged in (you can only edit your own) Unless they are an admin
 Frontend matches /vets design patterns
 Admin users can CRUD practices via UI
 Non-admin users only see read-only views

 React Routes:

 /pet_owners/(admin only)
 /pet_owners/{uuid}
 /pet_owners/{uuid}/edit