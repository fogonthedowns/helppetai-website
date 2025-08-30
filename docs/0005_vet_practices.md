Vet Practice Management - REST API & Frontend
Backend Requirements
REST Endpoints

GET /practices - List all practices (public, no auth)
GET /practices/{uuid} - View single practice (public, no auth)
POST /practices - Create practice (admin only)
PUT /practices/{uuid} - Update practice (admin only | no other role has access)
DELETE /practices/{uuid} - Delete practice (admin only | no other role has access)

Technical Specs

Use UUID primary keys (not numerical IDs)
Admin role authorization for CUD operations
Public access for read operations

Frontend Requirements
Pages/Components

Practice list page (public)
Practice detail page (public)
Practice create/edit form (admin only. no acesss to patients, vets, etc)
Admin practice management dashboard

Design

Follow existing /vets endpoint UI patterns
Responsive React components
Role-based component rendering (hide admin features for non-admins)

Acceptance Criteria

 All REST endpoints implemented with proper HTTP methods
 UUID-based routing works correctly
 Admin authentication enforced for create/edit/delete
 Public can view list and individual practices
 Frontend matches /vets design patterns
 Admin users can CRUD practices via UI
 Non-admin users only see read-only views