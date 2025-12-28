--
-- PostgreSQL database dump
--

\restrict m72bVMsTQKMXEC64ju8GmHVqqfmugXXmffjl9RHjAx1jrDNjfVsdDhzxbixRud2

-- Dumped from database version 17.7
-- Dumped by pg_dump version 17.7

-- Started on 2025-12-28 01:08:11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 217 (class 1259 OID 93074)
-- Name: admin_access_code; Type: TABLE; Schema: public; Owner: amimedne0229
--

CREATE TABLE public.admin_access_code (
    id integer NOT NULL,
    code character varying(100) NOT NULL,
    is_active boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.admin_access_code OWNER TO amimedne0229;

--
-- TOC entry 218 (class 1259 OID 93077)
-- Name: admin_access_code_id_seq; Type: SEQUENCE; Schema: public; Owner: amimedne0229
--

CREATE SEQUENCE public.admin_access_code_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.admin_access_code_id_seq OWNER TO amimedne0229;

--
-- TOC entry 4974 (class 0 OID 0)
-- Dependencies: 218
-- Name: admin_access_code_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: amimedne0229
--

ALTER SEQUENCE public.admin_access_code_id_seq OWNED BY public.admin_access_code.id;


--
-- TOC entry 219 (class 1259 OID 93078)
-- Name: admin_user; Type: TABLE; Schema: public; Owner: amimedne0229
--

CREATE TABLE public.admin_user (
    id integer NOT NULL,
    username character varying(80) NOT NULL,
    password_hash character varying(120) NOT NULL,
    is_active boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.admin_user OWNER TO amimedne0229;

--
-- TOC entry 220 (class 1259 OID 93081)
-- Name: admin_user_id_seq; Type: SEQUENCE; Schema: public; Owner: amimedne0229
--

CREATE SEQUENCE public.admin_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.admin_user_id_seq OWNER TO amimedne0229;

--
-- TOC entry 4975 (class 0 OID 0)
-- Dependencies: 220
-- Name: admin_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: amimedne0229
--

ALTER SEQUENCE public.admin_user_id_seq OWNED BY public.admin_user.id;


--
-- TOC entry 221 (class 1259 OID 93082)
-- Name: order; Type: TABLE; Schema: public; Owner: amimedne0229
--

CREATE TABLE public."order" (
    id character varying(20) NOT NULL,
    phone_number character varying(20) NOT NULL,
    customer_name character varying(100) NOT NULL,
    wilaya character varying(100) NOT NULL,
    address text NOT NULL,
    status character varying(50),
    total double precision NOT NULL,
    delivery_updates text,
    created_at timestamp without time zone
);


ALTER TABLE public."order" OWNER TO amimedne0229;

--
-- TOC entry 222 (class 1259 OID 93087)
-- Name: order_item; Type: TABLE; Schema: public; Owner: amimedne0229
--

CREATE TABLE public.order_item (
    id integer NOT NULL,
    order_id character varying(20) NOT NULL,
    product_id character varying(50) NOT NULL,
    product_name character varying(200) NOT NULL,
    quantity integer NOT NULL,
    price double precision NOT NULL,
    color character varying(50),
    image character varying(500),
    selected_color character varying(100) DEFAULT ''::character varying
);


ALTER TABLE public.order_item OWNER TO amimedne0229;

--
-- TOC entry 223 (class 1259 OID 93093)
-- Name: order_item_id_seq; Type: SEQUENCE; Schema: public; Owner: amimedne0229
--

CREATE SEQUENCE public.order_item_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.order_item_id_seq OWNER TO amimedne0229;

--
-- TOC entry 4976 (class 0 OID 0)
-- Dependencies: 223
-- Name: order_item_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: amimedne0229
--

ALTER SEQUENCE public.order_item_id_seq OWNED BY public.order_item.id;


--
-- TOC entry 224 (class 1259 OID 93094)
-- Name: product; Type: TABLE; Schema: public; Owner: amimedne0229
--

CREATE TABLE public.product (
    id character varying(50) NOT NULL,
    title character varying(200) NOT NULL,
    price double precision NOT NULL,
    brand character varying(100) NOT NULL,
    description text NOT NULL,
    model character varying(50) NOT NULL,
    frame_shape character varying(100),
    frame_material character varying(100),
    frame_color character varying(100),
    lenses character varying(200),
    protection character varying(200),
    dimensions character varying(50),
    images text,
    type character varying(50),
    quantity integer,
    created_at timestamp without time zone,
    popularity integer DEFAULT 0,
    discount_price double precision,
    discount_active boolean DEFAULT false,
    discount_start timestamp without time zone,
    discount_end timestamp without time zone,
    available_colors text DEFAULT '[]'::text,
    is_featured boolean DEFAULT false
);


ALTER TABLE public.product OWNER TO amimedne0229;

--
-- TOC entry 225 (class 1259 OID 93103)
-- Name: promo_code; Type: TABLE; Schema: public; Owner: amimedne0229
--

CREATE TABLE public.promo_code (
    id integer NOT NULL,
    code character varying(50) NOT NULL,
    discount_type character varying(20) NOT NULL,
    discount_value double precision NOT NULL,
    min_order_amount double precision,
    max_discount double precision,
    usage_limit integer,
    used_count integer,
    valid_from timestamp without time zone NOT NULL,
    valid_until timestamp without time zone NOT NULL,
    is_active boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.promo_code OWNER TO amimedne0229;

--
-- TOC entry 226 (class 1259 OID 93106)
-- Name: promo_code_id_seq; Type: SEQUENCE; Schema: public; Owner: amimedne0229
--

CREATE SEQUENCE public.promo_code_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.promo_code_id_seq OWNER TO amimedne0229;

--
-- TOC entry 4977 (class 0 OID 0)
-- Dependencies: 226
-- Name: promo_code_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: amimedne0229
--

ALTER SEQUENCE public.promo_code_id_seq OWNED BY public.promo_code.id;


--
-- TOC entry 4765 (class 2604 OID 93107)
-- Name: admin_access_code id; Type: DEFAULT; Schema: public; Owner: amimedne0229
--

ALTER TABLE ONLY public.admin_access_code ALTER COLUMN id SET DEFAULT nextval('public.admin_access_code_id_seq'::regclass);


--
-- TOC entry 4766 (class 2604 OID 93108)
-- Name: admin_user id; Type: DEFAULT; Schema: public; Owner: amimedne0229
--

ALTER TABLE ONLY public.admin_user ALTER COLUMN id SET DEFAULT nextval('public.admin_user_id_seq'::regclass);


--
-- TOC entry 4767 (class 2604 OID 93109)
-- Name: order_item id; Type: DEFAULT; Schema: public; Owner: amimedne0229
--

ALTER TABLE ONLY public.order_item ALTER COLUMN id SET DEFAULT nextval('public.order_item_id_seq'::regclass);


--
-- TOC entry 4773 (class 2604 OID 93110)
-- Name: promo_code id; Type: DEFAULT; Schema: public; Owner: amimedne0229
--

ALTER TABLE ONLY public.promo_code ALTER COLUMN id SET DEFAULT nextval('public.promo_code_id_seq'::regclass);


--
-- TOC entry 4959 (class 0 OID 93074)
-- Dependencies: 217
-- Data for Name: admin_access_code; Type: TABLE DATA; Schema: public; Owner: amimedne0229
--

COPY public.admin_access_code (id, code, is_active, created_at) FROM stdin;
6	//%_dOc.hAythAm-AmI(mEd)nE-0229_%//smIth2&&1!?!?!?	t	2025-12-01 00:55:09.136516
\.


--
-- TOC entry 4961 (class 0 OID 93078)
-- Dependencies: 219
-- Data for Name: admin_user; Type: TABLE DATA; Schema: public; Owner: amimedne0229
--

COPY public.admin_user (id, username, password_hash, is_active, created_at) FROM stdin;
6	amimedne0229	pbkdf2:sha256:600000$kKrvyxCMrEooIu9p$6adf5fb25125a039991d190d5a008579113675198b497ab9b527d5a2ed4ecf08	t	2025-12-01 00:45:02.765192
\.


--
-- TOC entry 4963 (class 0 OID 93082)
-- Dependencies: 221
-- Data for Name: order; Type: TABLE DATA; Schema: public; Owner: amimedne0229
--

COPY public."order" (id, phone_number, customer_name, wilaya, address, status, total, delivery_updates, created_at) FROM stdin;
ORD-782525	0795516111	med med	16	jfgcglyuhgpuijn	pending	14500	[{"date": "2025-12-20T06:31:05.466358", "status": "ordered", "message": "Order received"}]	2025-12-20 06:31:05.467998
\.


--
-- TOC entry 4964 (class 0 OID 93087)
-- Dependencies: 222
-- Data for Name: order_item; Type: TABLE DATA; Schema: public; Owner: amimedne0229
--

COPY public.order_item (id, order_id, product_id, product_name, quantity, price, color, image, selected_color) FROM stdin;
482	ORD-782525	women-sunglass-1	Cat Eye Sunglasses	1	14500		https://i.ibb.co/4C5PGSM/men-03.jpg	Black/Crystal
\.


--
-- TOC entry 4966 (class 0 OID 93094)
-- Dependencies: 224
-- Data for Name: product; Type: TABLE DATA; Schema: public; Owner: amimedne0229
--

COPY public.product (id, title, price, brand, description, model, frame_shape, frame_material, frame_color, lenses, protection, dimensions, images, type, quantity, created_at, popularity, discount_price, discount_active, discount_start, discount_end, available_colors, is_featured) FROM stdin;
women-eyeglass-3	Round Vintage	7200	Polar	Vintage-inspired round frames with lightweight construction.	Women	Round	Metal	Rose Gold	Clear (prescription ready)	Blue light filtering available	48-19-135	{"rose-gold": ["assets/images/women-eyeglass-3-rose-gold.jpg"], "silver": ["assets/images/women-eyeglass-3-silver.jpg"]}	eyeglasses	\N	2025-12-01 00:55:08.859615	0	\N	f	\N	\N	[{"name": "Rose Gold", "stock": 49, "images": ["assets/images/women-eyeglass-3-rose-gold.jpg"]}, {"name": "Silver", "stock": 40, "images": ["assets/images/women-eyeglass-3-silver.jpg"]}]	t
kids-sunglass-2	Mini Aviator	5200	Ray-Ban	Mini version of classic aviator sunglasses, perfect for kids.	Kids	Aviator	Flexible Metal	Silver	Brown gradient	100% UV protection, Category 2	44-15-125	{"silver": ["assets/images/kids-sunglass-2-silver.jpg"], "gold": ["assets/images/kids-sunglass-2-gold.jpg"]}	sunglasses	\N	2025-12-01 00:55:08.861306	0	\N	f	\N	\N	[{"name": "Silver", "stock": 57, "images": ["assets/images/kids-sunglass-2-silver.jpg"]}, {"name": "Gold", "stock": 59, "images": ["assets/images/kids-sunglass-2-gold.jpg"]}]	t
women-eyeglass-2	Geometric Hexagon	8400	BURBERRY	Modern hexagonal frames with unique geometric design.	Women	Hexagonal	Acetate	Tortoise	Clear (prescription ready)	Scratch resistant	52-18-140	{"tortoise": ["assets/images/women-eyeglass-2-tortoise.jpg"], "blue": ["assets/images/women-eyeglass-2-blue.jpg"]}	eyeglasses	\N	2025-12-01 00:55:08.858745	0	\N	f	\N	\N	[{"name": "Tortoise", "stock": 38, "images": ["assets/images/women-eyeglass-2-tortoise.jpg"]}, {"name": "Blue", "stock": 49, "images": ["assets/images/women-eyeglass-2-blue.jpg"]}]	t
women-eyeglass-1	Designer Cat Eye	9800	Versace	Fashionable cat eye frames with intricate details and comfortable fit.	Women	Cat Eye	Acetate	Clear Pink	Clear (prescription ready)	Anti-reflective coating	50-17-135	{"pink": ["assets/images/women-eyeglass-1-pink.jpg"], "black": ["assets/images/women-eyeglass-1-black.jpg"]}	eyeglasses	\N	2025-12-01 00:55:08.857749	0	\N	f	\N	\N	[{"name": "Clear Pink", "stock": 48, "images": ["assets/images/women-eyeglass-1-pink.jpg"]}, {"name": "Black", "stock": 50, "images": ["assets/images/women-eyeglass-1-black.jpg"]}]	t
men-eyeglass-3	Modern Square	11200	Gucci	Contemporary square frames with luxury details and comfortable fit.	Men	Square	Acetate	Black/Gold	Clear (prescription ready)	Blue light filtering available	54-16-145	{"black": ["assets/images/men-eyeglass-3-black.jpg"], "brown": ["assets/images/men-eyeglass-3-brown.jpg"]}	eyeglasses	\N	2025-12-01 00:55:08.853414	0	\N	f	\N	\N	[{"name": "Black/Gold", "stock": 49, "images": ["assets/images/men-eyeglass-3-black.jpg"]}, {"name": "Brown", "stock": 39, "images": ["assets/images/men-eyeglass-3-brown.jpg"]}]	t
men-eyeglass-1	Professional Rectangle	8900	Hugo Boss	Sophisticated rectangular frames perfect for professional settings.	Men	Rectangle	Acetate/Metal	Black/Silver	Clear (prescription ready)	Scratch resistant coating	52-18-145	{"black": ["assets/images/men-eyeglass-1-black.jpg"], "brown": ["assets/images/men-eyeglass-1-brown.jpg"]}	eyeglasses	\N	2025-12-01 00:55:08.851501	0	\N	f	\N	\N	[{"name": "Black/Silver", "stock": 46, "images": ["assets/images/men-eyeglass-1-black.jpg"]}, {"name": "Brown", "stock": 45, "images": ["assets/images/men-eyeglass-1-brown.jpg"]}]	t
men-sunglass-3	Sport Polarized	18900	Oakley	High-performance sports sunglasses with polarized lenses for active lifestyle.	Men	Wrap-around	O-Matter	Matte Black	Polarized black	100% UV, Polarized, Impact resistant	58-20-135	{"black": ["assets/images/men-sunglass-3-black.jpg"], "blue": ["assets/images/men-sunglass-3-blue.jpg"]}	sunglasses	\N	2025-12-01 00:55:08.850392	0	\N	f	\N	\N	[{"name": "Matte Black", "stock": 54, "images": ["https://i.ibb.co/4C5PGSM/men-03.jpg", "https://i.ibb.co/JFmWXcLS/explore-image-02.jpg"]}, {"name": "Blue", "stock": 49, "images": ["assets/images/men-sunglass-3-blue.jpg"]}]	t
men-sunglass-2	Wayfarer Classic	12500	Ray-Ban	Iconic wayfarer design with durable frames and crystal clear lenses.	Men	Wayfarer	Acetate	Black	Green gradient	100% UV protection, Category 2	52-18-140	{"black": ["assets/images/men-sunglass-2-black.jpg"], "brown": ["assets/images/men-sunglass-2-brown.jpg"]}	sunglasses	\N	2025-12-01 00:55:08.849109	0	10000	t	\N	\N	[{"name": "Black", "stock": 36, "images": ["https://i.ibb.co/4C5PGSM/men-03.jpg", "https://i.ibb.co/JFmWXcLS/explore-image-02.jpg"]}, {"name": "Brown", "stock": 38, "images": ["assets/images/men-sunglass-2-brown.jpg"]}]	t
women-sunglass-2	Oversized Square	13200	Prada	Chic oversized square sunglasses for maximum coverage and style.	Women	Square	Acetate	Brown	Grey gradient	100% UV protection, Category 3	58-14-140	{"brown": ["assets/images/women-sunglass-2-brown.jpg"], "black": ["assets/images/women-sunglass-2-black.jpg"]}	sunglasses	\N	2025-12-01 00:55:08.855235	0	\N	f	\N	\N	[{"name": "Brown", "stock": 39, "images": ["assets/images/women-sunglass-2-brown.jpg"]}, {"name": "Black", "stock": 37, "images": ["assets/images/women-sunglass-2-black.jpg"]}]	t
kids-sunglass-3	Character Round	3800	BURBERRY	Fun round sunglasses with character designs on the temples.	Kids	Round	Plastic	Multicolor	Blue mirror	100% UV protection, Flexible frames	42-14-120	{"blue": ["assets/images/kids-sunglass-3-blue.jpg"], "pink": ["assets/images/kids-sunglass-3-pink.jpg"]}	sunglasses	\N	2025-12-01 00:55:08.862268	0	\N	f	\N	\N	[{"name": "Blue", "stock": 86, "images": ["assets/images/kids-sunglass-3-blue.jpg"]}, {"name": "Pink", "stock": 88, "images": ["assets/images/kids-sunglass-3-pink.jpg"]}]	t
kids-sunglass-1	Colorful Wrap-around	4500	Polar	Fun colorful sunglasses with wrap-around design for active kids.	Kids	Wrap-around	Flexible Plastic	Blue/Red	Smoke grey	100% UV protection, Shatterproof	45-16-120	{"blue": ["assets/images/kids-sunglass-1-blue.jpg"], "red": ["assets/images/kids-sunglass-1-red.jpg"]}	sunglasses	\N	2025-12-01 00:55:08.860462	0	\N	f	\N	\N	[{"name": "Blue", "stock": 79, "images": ["assets/images/kids-sunglass-1-blue.jpg"]}, {"name": "Red", "stock": 68, "images": ["assets/images/kids-sunglass-1-red.jpg"]}]	t
women-sunglass-3	Aviator with Rhinestones	16800	Versace	Luxury aviator sunglasses with signature Medusa logo and rhinestone details.	Women	Aviator	Metal	Gold	Mirrored blue	100% UV protection, Category 3	56-16-140	{"gold": ["assets/images/women-sunglass-3-gold.jpg"], "silver": ["assets/images/women-sunglass-3-silver.jpg"]}	sunglasses	\N	2025-12-01 00:55:08.856507	0	\N	f	\N	\N	[{"name": "Gold", "stock": 48, "images": ["assets/images/women-sunglass-3-gold.jpg"]}, {"name": "Silver", "stock": 46, "images": ["assets/images/women-sunglass-3-silver.jpg"]}]	t
kids-eyeglass-2	Round Flexible	3900	BURBERRY	Soft round frames with spring hinges for comfortable fit.	Kids	Round	Flexible Plastic	Pink/Purple	Clear (prescription ready)	Impact resistant, Spring hinges	38-15-115	{"pink": ["assets/images/kids-eyeglass-2-pink.jpg"], "purple": ["assets/images/kids-eyeglass-2-purple.jpg"]}	eyeglasses	\N	2025-12-01 00:55:08.865128	0	\N	f	\N	\N	[{"name": "Pink", "stock": 80, "images": ["assets/images/kids-eyeglass-2-pink.jpg"]}, {"name": "Purple", "stock": 78, "images": ["assets/images/kids-eyeglass-2-purple.jpg"]}]	t
kids-eyeglass-1	Flexible Rectangle	4200	Polar	Durable and flexible rectangular frames designed for active kids.	Kids	Rectangle	Flexible Plastic	Blue	Clear (prescription ready)	Shatterproof lenses, Flexible frames	40-14-120	{"blue": ["assets/images/kids-eyeglass-1-blue.jpg"], "red": ["assets/images/kids-eyeglass-1-red.jpg"]}	eyeglasses	\N	2025-12-01 00:55:08.864141	0	\N	f	\N	\N	[{"name": "Blue", "stock": 69, "images": ["assets/images/kids-eyeglass-1-blue.jpg"]}, {"name": "Red", "stock": 67, "images": ["assets/images/kids-eyeglass-1-red.jpg"]}]	t
men-sunglass-1	Classic Aviator Sunglasses	13900	Ray-Ban	Timeless aviator style with premium UV protection and comfortable fit.	Men	Aviator	Stainless Steel	Gold	Smoke gradient	100% UV protection, Category 3	55-18-145	{"black": ["assets/images/men-sunglass-1-black.jpg"], "gold": ["assets/images/men-sunglass-1-gold.jpg"]}	sunglasses	\N	2025-12-01 00:55:08.846121	0	10000	f	\N	\N	[{"name": "black", "stock": 69, "images": ["assets/images/kids-eyeglass-1-blue.jpg"]}, {"name": "rose", "stock": 46, "images": ["assets/images/kids-eyeglass-1-blue.jpg"]}]	t
women-sunglass-1	Cat Eye Sunglasses	14500	Gucci	Elegant cat eye design with sophisticated styling for modern women.	Women	Cat Eye	Acetate	Black/Crystal	Brown gradient	100% UV protection, Category 3	52-16-135	{"black": ["assets/images/women-sunglass-1-black.jpg"], "red": ["assets/images/women-sunglass-1-red.jpg"]}	sunglasses	\N	2025-12-01 00:55:08.854306	0	\N	f	\N	\N	[{"name": "Black/Crystal", "stock": 88, "images": ["https://i.ibb.co/4C5PGSM/men-03.jpg", "https://i.ibb.co/JFmWXcLS/explore-image-02.jpg", "https://i.ibb.co/JFmWXcLS/explore-image-02.jpg", "https://i.ibb.co/JFmWXcLS/explore-image-02.jpg", "https://i.ibb.co/JFmWXcLS/explore-image-02.jpg", "https://i.ibb.co/JFmWXcLS/explore-image-02.jpg"]}, {"name": "Red", "stock": 48, "images": ["assets/images/women-sunglass-1-red.jpg"]}]	t
kids-eyeglass-3	Oval Character	4800	Polar	Fun oval frames with character themes and comfortable nose pads.	Kids	Oval	Plastic	Green/Yellow	Clear (prescription ready)	Scratch resistant, Soft nose pads	41-13-118	{"green": ["assets/images/kids-eyeglass-3-green.jpg"], "yellow": ["assets/images/kids-eyeglass-3-yellow.jpg"]}	eyeglasses	\N	2025-12-01 00:55:08.865964	0	\N	f	\N	\N	[{"name": "Green", "stock": 66, "images": ["https://i.ibb.co/4C5PGSM/men-03.jpg", "https://i.ibb.co/JFmWXcLS/explore-image-02.jpg"]}]	t
men-eyeglass-2	Classic Round	7600	Polar	Vintage-inspired round frames with modern comfort features.	Men	Round	Acetate	Tortoise	Clear (prescription ready)	Anti-reflective coating	50-19-140	{"tortoise": ["assets/images/men-eyeglass-2-tortoise.jpg"], "black": ["assets/images/men-eyeglass-2-black.jpg"]}	eyeglasses	\N	2025-12-01 00:55:08.85248	0	\N	f	\N	\N	[{"name": "black", "stock": 42, "images": ["https://i.ibb.co/4C5PGSM/men-03.jpg", "https://i.ibb.co/JFmWXcLS/explore-image-02.jpg"]}, {"name": "red", "stock": 49, "images": ["https://i.ibb.co/4C5PGSM/men-03.jpg", "https://i.ibb.co/JFmWXcLS/explore-image-02.jpg"]}]	t
\.


--
-- TOC entry 4967 (class 0 OID 93103)
-- Dependencies: 225
-- Data for Name: promo_code; Type: TABLE DATA; Schema: public; Owner: amimedne0229
--

COPY public.promo_code (id, code, discount_type, discount_value, min_order_amount, max_discount, usage_limit, used_count, valid_from, valid_until, is_active, created_at) FROM stdin;
\.


--
-- TOC entry 4978 (class 0 OID 0)
-- Dependencies: 218
-- Name: admin_access_code_id_seq; Type: SEQUENCE SET; Schema: public; Owner: amimedne0229
--

SELECT pg_catalog.setval('public.admin_access_code_id_seq', 6, true);


--
-- TOC entry 4979 (class 0 OID 0)
-- Dependencies: 220
-- Name: admin_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: amimedne0229
--

SELECT pg_catalog.setval('public.admin_user_id_seq', 6, true);


--
-- TOC entry 4980 (class 0 OID 0)
-- Dependencies: 223
-- Name: order_item_id_seq; Type: SEQUENCE SET; Schema: public; Owner: amimedne0229
--

SELECT pg_catalog.setval('public.order_item_id_seq', 578, true);


--
-- TOC entry 4981 (class 0 OID 0)
-- Dependencies: 226
-- Name: promo_code_id_seq; Type: SEQUENCE SET; Schema: public; Owner: amimedne0229
--

SELECT pg_catalog.setval('public.promo_code_id_seq', 22, true);


--
-- TOC entry 4775 (class 2606 OID 93112)
-- Name: admin_access_code admin_access_code_code_key; Type: CONSTRAINT; Schema: public; Owner: amimedne0229
--

ALTER TABLE ONLY public.admin_access_code
    ADD CONSTRAINT admin_access_code_code_key UNIQUE (code);


--
-- TOC entry 4777 (class 2606 OID 93114)
-- Name: admin_access_code admin_access_code_pkey; Type: CONSTRAINT; Schema: public; Owner: amimedne0229
--

ALTER TABLE ONLY public.admin_access_code
    ADD CONSTRAINT admin_access_code_pkey PRIMARY KEY (id);


--
-- TOC entry 4780 (class 2606 OID 93116)
-- Name: admin_user admin_user_pkey; Type: CONSTRAINT; Schema: public; Owner: amimedne0229
--

ALTER TABLE ONLY public.admin_user
    ADD CONSTRAINT admin_user_pkey PRIMARY KEY (id);


--
-- TOC entry 4782 (class 2606 OID 93118)
-- Name: admin_user admin_user_username_key; Type: CONSTRAINT; Schema: public; Owner: amimedne0229
--

ALTER TABLE ONLY public.admin_user
    ADD CONSTRAINT admin_user_username_key UNIQUE (username);


--
-- TOC entry 4794 (class 2606 OID 93120)
-- Name: order_item order_item_pkey; Type: CONSTRAINT; Schema: public; Owner: amimedne0229
--

ALTER TABLE ONLY public.order_item
    ADD CONSTRAINT order_item_pkey PRIMARY KEY (id);


--
-- TOC entry 4790 (class 2606 OID 93122)
-- Name: order order_pkey; Type: CONSTRAINT; Schema: public; Owner: amimedne0229
--

ALTER TABLE ONLY public."order"
    ADD CONSTRAINT order_pkey PRIMARY KEY (id);


--
-- TOC entry 4804 (class 2606 OID 93124)
-- Name: product product_pkey; Type: CONSTRAINT; Schema: public; Owner: amimedne0229
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT product_pkey PRIMARY KEY (id);


--
-- TOC entry 4810 (class 2606 OID 93126)
-- Name: promo_code promo_code_code_key; Type: CONSTRAINT; Schema: public; Owner: amimedne0229
--

ALTER TABLE ONLY public.promo_code
    ADD CONSTRAINT promo_code_code_key UNIQUE (code);


--
-- TOC entry 4812 (class 2606 OID 93128)
-- Name: promo_code promo_code_pkey; Type: CONSTRAINT; Schema: public; Owner: amimedne0229
--

ALTER TABLE ONLY public.promo_code
    ADD CONSTRAINT promo_code_pkey PRIMARY KEY (id);


--
-- TOC entry 4778 (class 1259 OID 93129)
-- Name: idx_admin_code; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_admin_code ON public.admin_access_code USING btree (code);


--
-- TOC entry 4783 (class 1259 OID 93130)
-- Name: idx_admin_user; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_admin_user ON public.admin_user USING btree (username);


--
-- TOC entry 4784 (class 1259 OID 93131)
-- Name: idx_order_created; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_order_created ON public."order" USING btree (created_at);


--
-- TOC entry 4785 (class 1259 OID 93132)
-- Name: idx_order_phone; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_order_phone ON public."order" USING btree (phone_number);


--
-- TOC entry 4786 (class 1259 OID 93133)
-- Name: idx_order_phone_created; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_order_phone_created ON public."order" USING btree (phone_number, created_at);


--
-- TOC entry 4787 (class 1259 OID 93134)
-- Name: idx_order_status; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_order_status ON public."order" USING btree (status);


--
-- TOC entry 4788 (class 1259 OID 93135)
-- Name: idx_order_status_created; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_order_status_created ON public."order" USING btree (status, created_at);


--
-- TOC entry 4791 (class 1259 OID 93136)
-- Name: idx_orderitem_order; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_orderitem_order ON public.order_item USING btree (order_id);


--
-- TOC entry 4792 (class 1259 OID 93137)
-- Name: idx_orderitem_product; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_orderitem_product ON public.order_item USING btree (product_id);


--
-- TOC entry 4795 (class 1259 OID 93138)
-- Name: idx_product_brand; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_product_brand ON public.product USING btree (brand);


--
-- TOC entry 4796 (class 1259 OID 93139)
-- Name: idx_product_brand_model; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_product_brand_model ON public.product USING btree (brand, model);


--
-- TOC entry 4797 (class 1259 OID 93140)
-- Name: idx_product_created; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_product_created ON public.product USING btree (created_at);


--
-- TOC entry 4798 (class 1259 OID 93141)
-- Name: idx_product_discount; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_product_discount ON public.product USING btree (discount_active, discount_end);


--
-- TOC entry 4799 (class 1259 OID 93142)
-- Name: idx_product_featured; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_product_featured ON public.product USING btree (is_featured);


--
-- TOC entry 4800 (class 1259 OID 93143)
-- Name: idx_product_model; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_product_model ON public.product USING btree (model);


--
-- TOC entry 4801 (class 1259 OID 93144)
-- Name: idx_product_model_featured; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_product_model_featured ON public.product USING btree (model, is_featured);


--
-- TOC entry 4802 (class 1259 OID 93145)
-- Name: idx_product_type; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_product_type ON public.product USING btree (type);


--
-- TOC entry 4805 (class 1259 OID 93146)
-- Name: idx_promo_active; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_promo_active ON public.promo_code USING btree (is_active);


--
-- TOC entry 4806 (class 1259 OID 93147)
-- Name: idx_promo_code; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_promo_code ON public.promo_code USING btree (code);


--
-- TOC entry 4807 (class 1259 OID 93148)
-- Name: idx_promo_usage; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_promo_usage ON public.promo_code USING btree (usage_limit, used_count);


--
-- TOC entry 4808 (class 1259 OID 93149)
-- Name: idx_promo_valid; Type: INDEX; Schema: public; Owner: amimedne0229
--

CREATE INDEX idx_promo_valid ON public.promo_code USING btree (valid_from, valid_until);


--
-- TOC entry 4813 (class 2606 OID 93150)
-- Name: order_item order_item_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: amimedne0229
--

ALTER TABLE ONLY public.order_item
    ADD CONSTRAINT order_item_order_id_fkey FOREIGN KEY (order_id) REFERENCES public."order"(id);


-- Completed on 2025-12-28 01:08:11

--
-- PostgreSQL database dump complete
--

\unrestrict m72bVMsTQKMXEC64ju8GmHVqqfmugXXmffjl9RHjAx1jrDNjfVsdDhzxbixRud2

