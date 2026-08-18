Salon SaaS — Complete Software 
Blueprint 
1. Product Positioning 
Core idea: 
Ek single web platform jahan salon owner apna customer, leads, appointments, staff, 
services, inventory, billing, WhatsApp communication aur marketing manage kar sake. 
Main users 
1. Super Admin — SaaS owner 
2. Salon Owner 
3. Branch Manager 
4. Receptionist 
5. Staff / Beautician 
6. Customer — booking page/app side 
 
2. Overall System Architecture 
                   SALON SaaS 
                        │ 
        ┌───────────────┼────────────────┐ 
        │               │                │ 
     SALON OWNER      STAFF           CUSTOMER 
        │               │                │ 
        └───────────────┼────────────────┘ 
                        │ 
                    DASHBOARD 
                        │ 
 ┌─────────┬────────┬────────┬─────────┬──────────┐ 
 │         │        │        │         │          │ 
 CRM   Appointments Staff   Services  Inventory  Billing 
 │         │        │        │         │          │ 
 └─────────┴────────┴────────┴─────────┴──────────┘ 
                        │ 
              WhatsApp / SMS / Email 
                        │ 
                   Marketing 
                        │ 
                   Analytics 
 
 
3. Login & Onboarding 
Login 
● Email/mobile 
● Password 
● Forgot password 
● OTP login 
● Google login 
● Remember me 
Salon onboarding 
First login ke baad: 
Step 1: Salon name 
Step 2: Logo 
Step 3: Address 
Step 4: Contact details 
Step 5: Business hours 
Step 6: Services 
Step 7: Staff 
Step 8: Payment methods 
Step 9: WhatsApp connection 
Step 10: Booking page setup 
Finally: 
Your salon is ready to accept bookings. 
 
4. Main Dashboard 
Dashboard sabse important screen hogi. 
Top cards 
● Today's Revenue 
● Today's Appointments 
● New Leads 
● New Customers 
● Pending Payments 
● Low Stock 
Appointment section 
Today's Schedule 
09:00  Priya     Hair Cut       
10:00  Neha      Facial         
Riya 
Pooja 
11:30  Aarti     Hair Colour    Riya 
Status: 
● Confirmed 
● Waiting 
● In Service 
● Completed 
● Cancelled 
● No Show 
Revenue chart 
● Today 
● This Week 
● This Month 
● Custom Range 
Dashboard insights 
Revenue ↑ 18% 
Appointments ↑ 12% 
New Customers ↑ 24% 
Repeat Customers ↓ 5% 
5. Appointment Management 
Calendar 
Views: 
● Day 
● Week 
● Month 
Filters: 
● Staff 
● Service 
● Branch 
● Status 
Create Appointment 
Fields: 
Customer 
Service 
Staff 
Date 
Time 
Duration 
Price 
Discount 
Advance 
Notes 
Appointment status 
Booked 
↓ 
Confirmed 
↓ 
Arrived 
↓ 
In Service 
↓ 
Completed 
↓ 
Paid 
Automatic actions 
Booking hone ke baad: 
WhatsApp 
Your appointment is confirmed for 4:00 PM. 
1 day before: 
Reminder: Your salon appointment is tomorrow at 4 PM. 
After appointment: 
Thank you for visiting. Please rate your experience. 
6. Customer CRM 
Customer database is product ka core hoga. 
Customer profile 
Name 
Mobile 
Email 
Gender 
DOB 
Anniversary 
Address 
Source 
Notes 
Customer history 
● Appointments 
● Services 
● Purchases 
● Payments 
● Discounts 
● Complaints 
● Reviews 
● WhatsApp conversations 
● Membership 
● Packages 
Customer segmentation 
Automatically create: 
New Customers 
VIP Customers 
Regular Customers 
Inactive Customers 
High Spending Customers 
Birthday This Month 
No Visit >30 Days 
No Visit >60 Days 
7. Lead Management / CRM 
Salon ko leads multiple channels se milenge. 
Lead sources 
● Instagram 
● Facebook 
● Google 
● Website 
● WhatsApp 
● Phone 
● Referral 
● Walk-in 
● Advertisement 
Lead pipeline 
New Lead 
↓ 
Contacted 
↓ 
Interested 
↓ 
Appointment Booked 
↓ 
Visited 
↓ 
Converted 
Lead dashboard 
Track: 
● Total leads 
● New leads 
● Contacted 
● Converted 
● Lost 
● Conversion % 
● Revenue from leads 
Example: 
Instagram — 120 leads 
48 appointments 
32 customers 
₹78,000 revenue 
8. Services Management 
Owner services create karega. 
Service fields 
Service Name 
Category 
Price 
Duration 
Description 
Tax 
Gender 
Available Staff 
Branch 
Example: 
Hair Cut 
₹500 
30 minutes 
Hair Colour 
₹2,500 
120 minutes 
9. Packages 
Example: 
Hair Care Package 
● Hair Cut 
● Hair Spa 
● Hair Wash 
Regular price: ₹2,000 
Package: ₹1,599 
System automatically tracks: 
3 services included 
2 used 
1 remaining 
10. Membership System 
Salon membership: 
Gold Membership 
₹4,999/year 
Benefits: 
● 15% service discount 
● Free consultation 
● Priority booking 
● Birthday benefit 
System tracks: 
● Start date 
● Expiry date 
● Benefits used 
● Remaining benefits 
Automatic reminder: 
Your membership expires in 7 days. 
11. Staff Management 
Staff profile 
Name 
Photo 
Mobile 
Role 
Services 
Branch 
Joining Date 
Salary 
Commission % 
Working Hours 
Staff roles 
● Beautician 
● Hair Stylist 
● Makeup Artist 
● Receptionist 
● Manager 
Staff calendar 
Each staff member ka availability. 
System appointment book karte waqt only available staff show karega. 
12. Staff Commission 
Example: 
Service: 
Hair Colour = ₹2,500 
Staff commission = 20% 
Commission: 
₹500 
Dashboard: 
Staff Revenue: ₹85,000 
Commission: ₹17,000 
Services Completed: 42 
13. Attendance 
Staff: 
● Check-in 
● Check-out 
● Late 
● Half-day 
● Leave 
● Holiday 
Monthly report: 
Working Days 
Present 
Absent 
Leave 
Late 
Overtime 
14. Inventory Management 
Inventory ko service consumption se connect karna bahut powerful feature hoga. 
Example: 
Hair Colour service: 
Hair Colour Product → 50ml 
Developer → 50ml 
Jab service complete hogi: 
Stock automatically reduce. 
Inventory modules 
● Products 
● Categories 
● Suppliers 
● Purchase 
● Stock In 
● Stock Out 
● Adjustments 
● Expiry 
● Low stock 
Product 
Product Name 
SKU 
Category 
Supplier 
Purchase Price 
Selling Price 
Current Stock 
Minimum Stock 
Expiry 
15. Supplier Management 
Supplier profile: 
● Name 
● Company 
● Mobile 
● Email 
● GSTIN 
● Address 
Purchase history: 
Product 
Quantity 
Price 
Tax 
Total 
Date 
16. Billing / POS 
Receptionist appointment complete hone ke baad: 
Generate Bill 
Hair Cut          
Hair Spa         
Product           
₹500 
₹1,200 
₹300 ---------------------- 
Subtotal         
Discount           
GST                
₹2,000 
₹200 
xxx ---------------------- 
Total            
₹xxxx 
Payment: 
● Cash 
● UPI 
● Card 
● Bank 
● Online 
● Split payment 
17. Expense Management 
Salon owner ko sirf revenue nahi, profit bhi dikhna chahiye. 
Expenses: 
● Rent 
● Electricity 
● Staff salary 
● Product purchase 
● Marketing 
● Maintenance 
● Other 
Dashboard: 
Revenue       
Expenses      
₹5,20,000 
₹2,10,000 
Gross Profit  ₹3,10,000 
18. WhatsApp Automation 
Ye product ka major USP ho sakta hai. 
Transactional 
● Booking confirmation 
● Reminder 
● Cancellation 
● Rescheduling 
● Invoice 
● Payment confirmation 
● Feedback request 
Marketing 
● Birthday 
● Anniversary 
● Festival 
● New service 
● Discount 
● Membership renewal 
● Inactive customer 
Automation example 
Customer inactive 45 days 
          ↓ 
Automation triggered 
          ↓ 
WhatsApp message 
          ↓ 
Customer clicks "Book Now" 
          ↓ 
Booking page 
          ↓ 
Appointment 
 
 
19. Marketing Campaigns 
Owner campaign create kare: 
Campaign Name 
Audience 
Message 
Offer 
Schedule 
Audience: 
Customers who haven't visited in 60 days. 
Message automatically sent. 
Campaign analytics 
● Sent 
● Delivered 
● Read 
● Clicked 
● Booked 
● Revenue generated 
20. Customer Booking Website 
Har salon ko ek booking URL milega: 
yourbrand.salonapp.com 
Customer sees: 
Salon 
★★★★★ 
Select Service 
Hair 
Skin 
Nails 
Makeup 
Spa 
↓ 
Select Staff 
↓ 
Select Date & Time 
↓ 
Customer Details 
↓ 
Payment / Advance 
↓ 
Booking Confirmed 
21. Online Booking Widget 
Salon apne existing website par bhi add kar sake: 
BOOK APPOINTMENT 
Click → booking popup. 
Instagram bio mein bhi booking link. 
Google Business Profile se bhi booking link use kiya ja sakta hai, subject to Google's available 
booking features/partners. 
22. Reviews & Feedback 
Appointment complete: 
How was your experience? 
★★★★★ 
Customer rating: 
5 stars 
Optional review. 
Owner dashboard: 
Average Rating: 4.8 
Total Reviews: 1,245 
23. Reports 
Sales Reports 
● Daily sales 
● Weekly 
● Monthly 
● Yearly 
● Branch-wise 
● Staff-wise 
● Service-wise 
Customer Reports 
● New customers 
● Repeat customers 
● Inactive customers 
● VIP customers 
Appointment Reports 
● Completed 
● Cancelled 
● No-show 
● Rescheduled 
Staff Reports 
● Revenue 
● Commission 
● Services 
● Attendance 
Inventory Reports 
● Stock value 
● Fast-moving products 
● Slow-moving products 
● Expiring products 
24. AI Features — Phase 2 
Yahan product normal salon software se alag ho sakta hai. 
AI Business Assistant 
Owner: 
"Meri sales last 3 months mein kaisi rahi?" 
AI: 
"Revenue increased 18% compared with the previous period." 
Owner: 
"Kaunse customers ko follow-up karna chahiye?" 
AI automatically list generate karega. 
Owner: 
"Sunday ke liye promotion banao." 
AI: 
Campaign + WhatsApp copy + Instagram caption. 
25. AI Customer Insights 
System identify kare: 
Customer A 
Average spend: ₹3,200 
Visit frequency: 42 days 
Last visit: 65 days ago 
AI recommendation: 
High-value inactive customer. Send reactivation offer. 
26. Multi-Branch Management 
Future mein: 
Business 
│ 
├── Ahmedabad Branch 
├── Vadodara Branch 
├── Surat Branch 
└── Mumbai Branch 
Owner all branches dekh sake. 
Branch manager only own branch access kare. 
27. User Permissions 
Very important. 
Owner 
Everything. 
Manager 
● Appointments 
● Staff 
● Customers 
● Sales 
● Inventory 
Receptionist 
● Appointments 
● Customers 
● Billing 
Staff 
● Own appointments 
● Own customers 
● Attendance 
● Commission 
Permissions granular honi chahiye: 
View 
Create 
Edit 
Delete 
Export 
28. Super Admin Panel 
Aap SaaS owner hongi. 
Super Admin Dashboard 
● Total salons 
● Active salons 
● Trial salons 
● Paid salons 
● MRR 
● Churn 
● New registrations 
● Active users 
● WhatsApp usage 
Salon management 
● View salon 
● Suspend 
● Activate 
● Change plan 
● Usage 
● Billing 
● Support 
29. SaaS Subscription System 
Example: 
Starter — ₹999/month 
● 1 Branch 
● 3 Staff 
● Appointments 
● CRM 
● Services 
● Basic Billing 
Growth — ₹1,999/month 
Everything in Starter + 
● 10 Staff 
● Inventory 
● Leads 
● WhatsApp automation 
● Reports 
● Marketing 
Professional — ₹3,999/month 
Everything + 
● Unlimited staff 
● Multi-branch 
● Advanced reports 
● Campaign automation 
● AI assistant 
● Advanced CRM 
Enterprise 
Custom pricing. 
30. Database Structure 
Core tables: 
users 
salons 
branches 
roles 
permissions 
customers 
leads 
lead_sources 
appointments 
appointment_services 
services 
service_categories 
packages 
package_services 
memberships 
staff 
staff_services 
staff_attendance 
staff_leaves 
staff_commissions 
products 
product_categories 
suppliers 
purchases 
purchase_items 
stock_transactions 
invoices 
invoice_items 
payments 
expenses 
campaigns 
campaign_recipients 
messages 
message_templates 
reviews 
notifications 
subscriptions 
subscription_plans 
payments 
settings 
audit_logs 
31. Important Relationships 
Salon 
├── Branches 
├── Staff 
├── Customers 
├── Services 
├── Products 
├── Appointments 
├── Invoices 
└── Campaigns 
Appointment: 
Customer 
+ 
Service 
+ 
Staff 
+ 
Branch 
↓ 
Appointment 
↓ 
Invoice 
↓ 
Payment 
32.## Recommended Tech Stack

> STACK OVERRIDE: This project uses Django + DRF + PostgreSQL.
> This section replaces the original Node/NestJS/Supabase recommendation.
> CLAUDE.md section 3 is the single authoritative stack.

Backend
Django 5.x + Django REST Framework (DRF)

API style
REST, API-first, all endpoints under /api/v1/

Frontend (later, optional)
Next.js + React + Tailwind CSS — consumes the DRF API

Database
PostgreSQL 15+

Authentication
● Django auth + djangorestframework-simplejwt (JWT access/refresh)
● OTP (mobile/email)

Storage
● Local file storage in dev
● django-storages + Amazon S3 in production

Payments
India ke liye:
● Razorpay (Python SDK)

WhatsApp
Official WhatsApp Business Platform / Cloud API (behind a provider interface)

Email
● Resend (REST API) or Amazon SES (via django-ses)

Notifications
● WhatsApp
● Email
● SMS

Async / scheduled tasks
● Celery + Redis + django-celery-beat (reminders, campaigns)

Hosting
● Backend: Railway / Render / Fly.io (managed Django host)
● Managed PostgreSQL: Neon / Railway / Supabase-as-DB / AWS RDS
● Static/media: S3 + CDN
● Frontend (if added): Vercel

33. MVP — Exactly What To Build First 
Main first version mein ye 10 modules banaunga: 
MVP 
1. Login & onboarding 
2. Dashboard 
3. Customers CRM 
4. Appointments 
5. Services 
6. Staff 
7. Billing/POS 
8. Basic inventory 
9. WhatsApp appointment notifications 
10. Reports 
Do not build initially: 
● AI 
● Advanced marketing automation 
● Multi-branch 
● Complex payroll 
● Advanced membership 
● Deep analytics 
Pehle actual salons se feedback lo. 
34. Version 2 
After initial customers: 
● Lead CRM 
● WhatsApp campaigns 
● Membership 
● Packages 
● Staff commission 
● Supplier management 
● Advanced inventory 
● Customer segmentation 
● Review management 
35. Version 3 
Then: 
● AI assistant 
● AI campaign generator 
● Multi-branch 
● Advanced analytics 
● Profit prediction 
● Customer churn prediction 
● Automated reactivation 
● White-label solution 
36. Most Important USP 
Market mein sirf: 
"Salon Appointment Software" 
mat banana. 
Positioning: 
"Run Your Entire Salon From One Dashboard." 
Aur product ke core mein ye loop hona chahiye: 
Lead → Customer → Appointment → Service → Payment → Review → Re-visit → 
Marketing → Repeat Revenue 
Yahi system salon owner ko one-time booking tool ke bajay complete business 
management platform dega. 
Suggested product name 
Temporary naam: 
SalonOS 
Tagline: 
Everything Your Salon Needs. One Simple Platform. 
Ya: 
SalonFlow 
Bookings. Customers. Staff. Sales. Growth. All in One. 