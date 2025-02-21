--
-- PostgreSQL database dump
--

-- Dumped from database version 14.15
-- Dumped by pg_dump version 14.15

-- Started on 2025-02-16 19:07:30 UTC

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
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
-- TOC entry 209 (class 1259 OID 16385)
-- Name: action_colours; Type: TABLE; Schema: public; Owner: fred
--

CREATE TABLE public.action_colours (
    id integer NOT NULL,
    name text,
    colour integer
);


ALTER TABLE public.action_colours OWNER TO fred;

--
-- TOC entry 210 (class 1259 OID 16390)
-- Name: action_colours_id_seq; Type: SEQUENCE; Schema: public; Owner: fred
--

CREATE SEQUENCE public.action_colours_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.action_colours_id_seq OWNER TO fred;

--
-- TOC entry 3423 (class 0 OID 0)
-- Dependencies: 210
-- Name: action_colours_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fred
--

ALTER SEQUENCE public.action_colours_id_seq OWNED BY public.action_colours.id;


--
-- TOC entry 211 (class 1259 OID 16391)
-- Name: commands; Type: TABLE; Schema: public; Owner: fred
--

CREATE TABLE public.commands (
    id integer NOT NULL,
    name text,
    content text,
    attachment text
);


ALTER TABLE public.commands OWNER TO fred;

--
-- TOC entry 212 (class 1259 OID 16396)
-- Name: commands_id_seq; Type: SEQUENCE; Schema: public; Owner: fred
--

CREATE SEQUENCE public.commands_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.commands_id_seq OWNER TO fred;

--
-- TOC entry 3424 (class 0 OID 0)
-- Dependencies: 212
-- Name: commands_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fred
--

ALTER SEQUENCE public.commands_id_seq OWNED BY public.commands.id;


--
-- TOC entry 213 (class 1259 OID 16397)
-- Name: crashes; Type: TABLE; Schema: public; Owner: fred
--

CREATE TABLE public.crashes (
    id integer NOT NULL,
    name text,
    crash text,
    response text
);


ALTER TABLE public.crashes OWNER TO fred;

--
-- TOC entry 214 (class 1259 OID 16402)
-- Name: crashes_id_seq; Type: SEQUENCE; Schema: public; Owner: fred
--

CREATE SEQUENCE public.crashes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.crashes_id_seq OWNER TO fred;

--
-- TOC entry 3425 (class 0 OID 0)
-- Dependencies: 214
-- Name: crashes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fred
--

ALTER SEQUENCE public.crashes_id_seq OWNED BY public.crashes.id;


--
-- TOC entry 215 (class 1259 OID 16403)
-- Name: dialogflow; Type: TABLE; Schema: public; Owner: fred
--

CREATE TABLE public.dialogflow (
    id integer NOT NULL,
    intent_id text,
    data text,
    response text,
    has_followup boolean
);


ALTER TABLE public.dialogflow OWNER TO fred;

--
-- TOC entry 216 (class 1259 OID 16408)
-- Name: dialogflow_channels; Type: TABLE; Schema: public; Owner: fred
--

CREATE TABLE public.dialogflow_channels (
    id integer NOT NULL,
    channel_id bigint
);


ALTER TABLE public.dialogflow_channels OWNER TO fred;

--
-- TOC entry 217 (class 1259 OID 16411)
-- Name: dialogflow_channels_id_seq; Type: SEQUENCE; Schema: public; Owner: fred
--

CREATE SEQUENCE public.dialogflow_channels_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dialogflow_channels_id_seq OWNER TO fred;

--
-- TOC entry 3426 (class 0 OID 0)
-- Dependencies: 217
-- Name: dialogflow_channels_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fred
--

ALTER SEQUENCE public.dialogflow_channels_id_seq OWNED BY public.dialogflow_channels.id;


--
-- TOC entry 218 (class 1259 OID 16412)
-- Name: dialogflow_exception_roles; Type: TABLE; Schema: public; Owner: fred
--

CREATE TABLE public.dialogflow_exception_roles (
    id integer NOT NULL,
    role_id bigint
);


ALTER TABLE public.dialogflow_exception_roles OWNER TO fred;

--
-- TOC entry 219 (class 1259 OID 16415)
-- Name: dialogflow_exception_roles_id_seq; Type: SEQUENCE; Schema: public; Owner: fred
--

CREATE SEQUENCE public.dialogflow_exception_roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dialogflow_exception_roles_id_seq OWNER TO fred;

--
-- TOC entry 3427 (class 0 OID 0)
-- Dependencies: 219
-- Name: dialogflow_exception_roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fred
--

ALTER SEQUENCE public.dialogflow_exception_roles_id_seq OWNED BY public.dialogflow_exception_roles.id;


--
-- TOC entry 220 (class 1259 OID 16416)
-- Name: dialogflow_id_seq; Type: SEQUENCE; Schema: public; Owner: fred
--

CREATE SEQUENCE public.dialogflow_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dialogflow_id_seq OWNER TO fred;

--
-- TOC entry 3428 (class 0 OID 0)
-- Dependencies: 220
-- Name: dialogflow_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fred
--

ALTER SEQUENCE public.dialogflow_id_seq OWNED BY public.dialogflow.id;


--
-- TOC entry 221 (class 1259 OID 16417)
-- Name: media_only_channels; Type: TABLE; Schema: public; Owner: fred
--

CREATE TABLE public.media_only_channels (
    id integer NOT NULL,
    channel_id bigint
);


ALTER TABLE public.media_only_channels OWNER TO fred;

--
-- TOC entry 222 (class 1259 OID 16420)
-- Name: media_only_channels_id_seq; Type: SEQUENCE; Schema: public; Owner: fred
--

CREATE SEQUENCE public.media_only_channels_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.media_only_channels_id_seq OWNER TO fred;

--
-- TOC entry 3429 (class 0 OID 0)
-- Dependencies: 222
-- Name: media_only_channels_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fred
--

ALTER SEQUENCE public.media_only_channels_id_seq OWNED BY public.media_only_channels.id;


--
-- TOC entry 223 (class 1259 OID 16421)
-- Name: miscellaneous; Type: TABLE; Schema: public; Owner: fred
--

CREATE TABLE public.miscellaneous (
    id integer NOT NULL,
    key text,
    value text
);


ALTER TABLE public.miscellaneous OWNER TO fred;

--
-- TOC entry 224 (class 1259 OID 16426)
-- Name: miscellaneous_id_seq; Type: SEQUENCE; Schema: public; Owner: fred
--

CREATE SEQUENCE public.miscellaneous_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.miscellaneous_id_seq OWNER TO fred;

--
-- TOC entry 3430 (class 0 OID 0)
-- Dependencies: 224
-- Name: miscellaneous_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fred
--

ALTER SEQUENCE public.miscellaneous_id_seq OWNED BY public.miscellaneous.id;


--
-- TOC entry 225 (class 1259 OID 16427)
-- Name: rank_roles; Type: TABLE; Schema: public; Owner: fred
--

CREATE TABLE public.rank_roles (
    id integer NOT NULL,
    rank integer,
    role_id bigint
);


ALTER TABLE public.rank_roles OWNER TO fred;

--
-- TOC entry 226 (class 1259 OID 16430)
-- Name: rank_roles_id_seq; Type: SEQUENCE; Schema: public; Owner: fred
--

CREATE SEQUENCE public.rank_roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.rank_roles_id_seq OWNER TO fred;

--
-- TOC entry 3431 (class 0 OID 0)
-- Dependencies: 226
-- Name: rank_roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fred
--

ALTER SEQUENCE public.rank_roles_id_seq OWNED BY public.rank_roles.id;


--
-- TOC entry 227 (class 1259 OID 16431)
-- Name: reserved_commands; Type: TABLE; Schema: public; Owner: fred
--

CREATE TABLE public.reserved_commands (
    id integer NOT NULL,
    name text
);


ALTER TABLE public.reserved_commands OWNER TO fred;

--
-- TOC entry 228 (class 1259 OID 16436)
-- Name: reserved_commands_id_seq; Type: SEQUENCE; Schema: public; Owner: fred
--

CREATE SEQUENCE public.reserved_commands_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.reserved_commands_id_seq OWNER TO fred;

--
-- TOC entry 3432 (class 0 OID 0)
-- Dependencies: 228
-- Name: reserved_commands_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fred
--

ALTER SEQUENCE public.reserved_commands_id_seq OWNED BY public.reserved_commands.id;


--
-- TOC entry 229 (class 1259 OID 16437)
-- Name: role_perms; Type: TABLE; Schema: public; Owner: fred
--

CREATE TABLE public.role_perms (
    id integer NOT NULL,
    role_id bigint,
    perm_lvl integer,
    role_name text
);


ALTER TABLE public.role_perms OWNER TO fred;

--
-- TOC entry 230 (class 1259 OID 16442)
-- Name: role_perms_id_seq; Type: SEQUENCE; Schema: public; Owner: fred
--

CREATE SEQUENCE public.role_perms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.role_perms_id_seq OWNER TO fred;

--
-- TOC entry 3433 (class 0 OID 0)
-- Dependencies: 230
-- Name: role_perms_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fred
--

ALTER SEQUENCE public.role_perms_id_seq OWNED BY public.role_perms.id;


--
-- TOC entry 231 (class 1259 OID 16443)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: fred
--

CREATE SEQUENCE public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 2147483647
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO fred;

--
-- TOC entry 232 (class 1259 OID 16444)
-- Name: users; Type: TABLE; Schema: public; Owner: fred
--

CREATE TABLE public.users (
    id integer DEFAULT nextval('public.users_id_seq'::regclass) NOT NULL,
    user_id bigint,
    full_name text,
    message_count integer,
    xp_count double precision,
    xp_multiplier double precision,
    role_xp_multiplier double precision,
    rank integer,
    rank_role_id bigint,
    accepts_dms boolean
);


ALTER TABLE public.users OWNER TO fred;

--
-- TOC entry 3219 (class 2604 OID 16450)
-- Name: action_colours id; Type: DEFAULT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.action_colours ALTER COLUMN id SET DEFAULT nextval('public.action_colours_id_seq'::regclass);


--
-- TOC entry 3220 (class 2604 OID 16451)
-- Name: commands id; Type: DEFAULT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.commands ALTER COLUMN id SET DEFAULT nextval('public.commands_id_seq'::regclass);


--
-- TOC entry 3221 (class 2604 OID 16452)
-- Name: crashes id; Type: DEFAULT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.crashes ALTER COLUMN id SET DEFAULT nextval('public.crashes_id_seq'::regclass);


--
-- TOC entry 3222 (class 2604 OID 16453)
-- Name: dialogflow id; Type: DEFAULT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.dialogflow ALTER COLUMN id SET DEFAULT nextval('public.dialogflow_id_seq'::regclass);


--
-- TOC entry 3223 (class 2604 OID 16454)
-- Name: dialogflow_channels id; Type: DEFAULT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.dialogflow_channels ALTER COLUMN id SET DEFAULT nextval('public.dialogflow_channels_id_seq'::regclass);


--
-- TOC entry 3224 (class 2604 OID 16455)
-- Name: dialogflow_exception_roles id; Type: DEFAULT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.dialogflow_exception_roles ALTER COLUMN id SET DEFAULT nextval('public.dialogflow_exception_roles_id_seq'::regclass);


--
-- TOC entry 3225 (class 2604 OID 16456)
-- Name: media_only_channels id; Type: DEFAULT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.media_only_channels ALTER COLUMN id SET DEFAULT nextval('public.media_only_channels_id_seq'::regclass);


--
-- TOC entry 3226 (class 2604 OID 16457)
-- Name: miscellaneous id; Type: DEFAULT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.miscellaneous ALTER COLUMN id SET DEFAULT nextval('public.miscellaneous_id_seq'::regclass);


--
-- TOC entry 3227 (class 2604 OID 16458)
-- Name: rank_roles id; Type: DEFAULT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.rank_roles ALTER COLUMN id SET DEFAULT nextval('public.rank_roles_id_seq'::regclass);


--
-- TOC entry 3228 (class 2604 OID 16459)
-- Name: reserved_commands id; Type: DEFAULT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.reserved_commands ALTER COLUMN id SET DEFAULT nextval('public.reserved_commands_id_seq'::regclass);


--
-- TOC entry 3229 (class 2604 OID 16460)
-- Name: role_perms id; Type: DEFAULT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.role_perms ALTER COLUMN id SET DEFAULT nextval('public.role_perms_id_seq'::regclass);


--
-- TOC entry 3394 (class 0 OID 16385)
-- Dependencies: 209
-- Data for Name: action_colours; Type: TABLE DATA; Schema: public; Owner: fred
--

COPY public.action_colours (id, name, colour) FROM stdin;
1	red	15408413
2	orange	15436573
3	yellow	15529284
4	green	5357373
7	purple	7482326
8	pink	16087789
9	die	16711918
5	light blue	6414322
6	dark blue	2629304
\.


--
-- TOC entry 3396 (class 0 OID 16391)
-- Dependencies: 211
-- Data for Name: commands; Type: TABLE DATA; Schema: public; Owner: fred
--

COPY public.commands (id, name, content, attachment) FROM stdin;
1	source	<https://github.com/Feyko/FICSIT-Fred>	\N
2	.<	>.<	\N
3	kronos	Hi ! The Kronos Mod hasn't been updated and probably won't be. You might be interested in the Pak Utility Mod instead, which does a lot of the same things.	\N
4	super	<:lazy:642114479097905206>	\N
5	map	https://satisfactory-calculator.com/en/interactive-map	\N
6	acronym	https://github.com/satisfactorymodding/SatisfactoryAcronymVault	\N
7	invite	<https://bit.ly/SatisfactoryModding>	\N
8	smr	If you want to find mods or upload your own - check out the Satisfactory Mod Repo <https://ficsit.app/>	\N
211	steamepic	>epicsteam	\N
10	logs	You can find logs at different locations:\nIn your game folder. There is pre-launch-debug.log and SatisfactoryModLoader.log\nAt %localappdata%/FactoryGame/Saved/logs, where FactoryGame.log is located\nThe best way of gathering logs still remains to "generate debug info" via SMM	\N
16	fin	If you have any questions about Ficsit-Networks, want to know more info about it or share/yoink some scripts, Join the discord ! https://discord.gg/agwBPv6	\N
17	saveeditor	<https://github.com/Goz3rr/SatisfactorySaveEditor/releases>	\N
136	vanilla	To switch to vanilla (non-modded), hit the Mods on and off button that is right beside the `Profile` button.\n\nDo note uninstalling the mod manager will not uninstall mods from your game. you will then have to reinstall the mod manager to do so\n\nIf this does not remove the mods, go to `%appdata%\\SatisfactoryModManager\\profiles` and delete the `vanilla` folder, then restart SMM and turn mods on and back off.\n\nIf that still doesn't work, go to your game dir and delete the `FactoryGame\\Mods` folder	https://cdn.discordapp.com/attachments/555507339969560586/869416437335330826/unknown.png
20	w<	>w<	\N
22	factorygame.log	Hit windows + r . Enter `%localappdata%/FactoryGame/Saved/Logs` in the opened box then click on Ok. That will open a folder, send the file named `FactoryGame.log` from there	\N
23	deantendo	https://cdn.discordapp.com/attachments/319164249333039114/768441479952859186/summondeantendo2.gif	\N
36	sod	Hello! It seems like your question or issue is not mod related. For help with standard game related questions, issues, please use the official Satisfactory discord.\n\nhttps://discord.gg/satisfactory	\N
25	gbh	Get Back Here has been discontinued. You can still achieve the same effect with a mod that's in very early access, TweakIt ! Join the Discord for more info : https://discord.gg/FZPzq74	\N
26	modlist	List of C++ mods and their state + list of broken BP mods\n<https://docs.google.com/spreadsheets/d/1FUXLJ9D6PKFOkU__WuIUlkwIsms15BUGQkmwz-ImBcg/edit?usp=sharing>	\N
31	down	https://ficsit.app/ is down. The mod manager uses the website to download mods, which means it will not work for now. You can still launch your game and play with mods. Please be patient while we work on getting the website up again	\N
35	sad	<:sadalpaca:787662751018778625>	\N
37	smm	https://smm.ficsit.app/	\N
38	workshop	https://youtu.be/FkG749zfA2w	\N
33	cache	https://cdn.discordapp.com/attachments/555507339969560586/833748126467883048/unknown.png	\N
15	profiles	https://cdn.discordapp.com/attachments/555507339969560586/833748278456746014/unknown.png	\N
19	manifest	Open Steam, then go to your Steam folder/library (not your Satisfactory install folder), and delete `appmanifest_526870.acf`. Then verify the game files in Steam	\N
163	alpaca-time	\N	https://cdn.discordapp.com/attachments/862418592528203836/893538001110573086/xIK21PEgr8PV.gif
164	vanillaprofile	Somehow SMM managed to load mods into the Vanilla profile to fix this go to `%appdata%\\SatisfactoryModManager\\profiles` and delete the `vanilla` folder.\nAfter you did that restart SMM and the vanilla profile should work as intended again.	\N
29	versions	 	https://cdn.discordapp.com/attachments/834348739539238922/878384003491725342/unknown.png
30	:(	>:)	\N
155	engineupgrade	**TLDR: Mods don't work on the Experimental branch currently. Use Early Access instead**\n\nThe Experimental branch has been updated with a new version of Unreal Engine which breaks SML and some mods. If you want to test the engine upgrade (DX12/Vulkan/Conveyor rendering improvements) you can disable mods from SMM. If you want to keep playing with mods, use the Early Access branch which is the same as the previous Experimental version.\n\n*If you have just started using mods, and you have been playing on experimental for long, switching back to Early Access will break your saves, so we recommend that you just play without mods for the time being.*\nSee `>vanilla` for details.	\N
183	100+	>mm	\N
184	piracy	>zerotollerance	\N
185	sod-off	>sod	\N
186	steamexp	>steambranch	\N
187	scim	>map	\N
154	oldconfigs	The config folder since SML 3 is `SatisfactoryDir\\FactoryGame\\Configs` instead of the previous `SatisfactoryDir\\configs`. Delete the old folder and if you don't see the new folder run the game once and SML will generate it	\N
188	asking	>dataja	\N
189	making-mods	>modding	\N
190	makingmods	>modding	\N
191	outdated	>red	\N
192	powersuit	>nog	\N
193	persistantpaintables	>sirdigby	\N
194	pp	>sirdigby	\N
195	unifiedgrid	>sirdigby	\N
196	ug	>sirdigby	\N
197	debug-info	>debuginfo	\N
198	debug	>debuginfo	\N
48	epicsteam	There is no difference in the game files between the Epic and Steam "versions", they are exactly the same. However, on Epic you can have both the Early Access and the Experimental branches installed at the same time, while on Steam you can only choose one at a time	\N
214	steamverify	>verifysteam	\N
43	download	Trying to download the mod manager, but it's slow? That would be the fault of github, and as such there's nothing we can do about it. Some users have had luck using a VPN, proxy, or both.	\N
216	epicverify	>verifyepic	\N
47	modlist_moremachines	Click the link to see a list of mods which add more machines for you to build: https://ficsit.app/guide/FBePQ6bSrrD9vy	\N
49	bufferoverflow	This is an issue that can affect any mod that adds schematics with dependencies. It should be fixed in the next SML version. In the mean time, you can use Goz3rr's save editor's 'Deduplicate Schematics' cheat to get rid of the copies. https://github.com/Goz3rr/SatisfactorySaveEditor/releases	\N
50	smmhelp	Want to know more about the Satisfactory Mod Manager? See the guide here: https://ficsit.app/guide/NG4DD9UhWjMUK	\N
51	install	Need a guide to install the Satisfactory Mod Manager? Worried that it's not safe? Click here to read more: https://ficsit.app/guide/9aDEJRdmJsEBTJ	\N
53	mm	if you are getting issues or have a question with more milestones mod, Join it's discord! https://discord.gg/MrZ3TJKMEu	\N
217	microwave	>mwave	\N
56	bpcode	https://github.com/Archengius/BPPseudoCodeGen/tree/master	\N
57	playvanilla	The general feeling here is to leave the mods until you hit at least T6 or a few hundred hours. You only get to experience the game for the 1st time once. Best not to rob yourself of that. Of course; it's your gameplay, so do as you will, but many here feel that using mods immediately ruins the game in many ways. At most; maybe just use Quality of Life mods if you're determined to mod from the start. You can type >modlist_nocheat to get a link to a mod list, and >welcome to get a link to a new users guide to the mod manager and mods in general.	\N
58	commandlist	List of discord commands specific to this community: https://github.com/deantendo/community/raw/master/discordcommands.txt	\N
60	welcome	Hello new person!\n\n**Click the link for:**\nHow to get SMM\nHow to install SMM\nHow to use SMM\nHelp with mods\nOur recommendations for using mods\nIf mods work with EA or EXP\nMod list recommendations\nHelpful tips\n\nhttps://ficsit.app/guide/AYVEPJd3Fi1oxa	\N
62	zerotollerance	Nobody is entitled to pirate a game. Too expensive? Don't buy it.  Use the refund system to demo the game. Watch some gameplay videos. \n\n"But I can't afford it" then you cannot have it. Wait for a sale. \n\nRules of the server state zero tolerance to piracy. You are required to read the rules. Entering a discord server implies you have accepted the rules. \n\nWe need to be hard on pirates as we rely on CSS to make mods work. Do you think they'd bother to help us if we allowed pirates?	\N
63	happy	<:alpaca:576075398673203210>	\N
64	modularbuild	**1. What is modular build?**\nMost games come as one large file which is hard to change, but a smaller download. A modular build is the same game, but with all the different parts as its own set of files. Even though it means a slightly larger download it has many advantages...\n\n**2. Why is Satisfactory getting it?**\nThe modular build exists because we -the modding community- asked for it (and CSS are lovely to work with).\n\n**3. Why is it good?**\nIt'll help us make better mods, and modding a little easier. It will slightly speed-up mod loading times (not game loading times), and it also means we have more ways to make mods and features which would have been taken out before.\n\n**4. How will it make mods easier to make?**\nFor almost all normal mods which are quite simple, not much will change, but more complex mods will be easier to make as we can now access features which had previously been harder to work with\n\n**5. How can it help make better mods?**\nBecause now that less is taken out we can do things like add new Unreal Engine modules which aren't included with the game. This means we can add features and tools for mods.\n\n**6. Will i see any other benefits?**\nFor the average player and mod user? Not much. Slightly faster load times, but that's all. What you WILL see is better mods.\n\n**7. Is this going to delay the updated modding tools so that mods can be working and ready for update 4?**\nYes. But we still plan to get the tools ready in time for update 4. It'll be down to modders to get their mods working.	\N
65	legend	✅ : Line additions\n❌ : Line deletions\n📝 : Number of changed files\n📋 : Number of commits	\N
66	.>	<.<	\N
54	offscreen	The issue is that the window somehow got offscreen. To fix it you need to go in `%appdata%\\SatisfactoryModManager\\settings.json` and in `windowLocation` set the x and y to 0 to bring the window back on the screen. Restart SMM after you do that	\N
39	malware	The reason is that the mod manager does not have a certificate / detects as malware: \nThe certificate costs hundreds per year, those involved refuse to pay it. But rest assured; This community created it from scratch. We all use it. Provided you only get it via https://smm.ficsit.app we can assure you it is safe.\nSMM is open-source and can be found here: <https://github.com/satisfactorymodding/SatisfactoryModManager>	\N
46	creative	Want to play creative mode?\nHere would be a list of mods that should provide a creative mode like experience:\nhttps://ficsit.app/guide/8B8zfGtQXEF5i9	\N
52	qol	Want Quality of Life mods?\nHere would be a list of qol mods:\nhttps://ficsit.app/guide/4kk48ivCPtoL3K	\N
168	d3d	Please force the use of DirectX11 with your game by adding the -d3d11 argument to your game	\N
169	scim-support	https://discord.com/invite/0sFOD6GxFZRc1ad0	\N
161	debuginfo	In order to help you we need more information\nwe can get that additional Information when you go to the following setting, save the file and send the whole zip archive in this channel.	https://cdn.discordapp.com/attachments/834348739539238922/892086547820728381/debuginfo.png
72	qa	https://questions.satisfactorygame.com/	\N
73	dataja	https://dontasktoask.com/	\N
75	sftools	https://www.satisfactorytools.com/	\N
76	poggers	https://cdn.discordapp.com/attachments/555515791592652823/823093913782452254/poggers-128.png	\N
68	mwave	Microwave Power(Mwave) is the currently developed spiritual successor of Feyko's Wireless Power mod made by Deantendo, Kyrium and Hailun.\nIt has it's own category on Kyriums discord server.\nhttps://discord.gg/JsJ9XXWS7Q\n\nhttps://media.discordapp.net/attachments/891205565542436865/891298184255643658/unknown.png	\N
78	pins	Please read the pinned messages for answers to common questions	\N
44	tweakit	TweakIt is a WIP mod developed by Feyko. It allows anyone to write simple scripts that can change the game's values and more. Since it is very unstable at the moment, the only way to get it is through the mod's Discord server : https://discord.gg/FZPzq74\nPlease read the faq there before asking questions	\N
91	smart	For Smart! bug reports, join the Smart discord: https://discord.gg/SgXY4CwXYw	\N
86	moarupdates	MoarFactory (and any other very popular mod) is unlikely to get updated.	\N
88	doesxwork	You can see what mods are currently update at <https://ficsit.app/> Mods that aren't marked as outdated are updated for the Update 4	\N
69	ui-time	**I SUMMON THEE, <@!293484684787056640> **	https://cdn.discordapp.com/attachments/834348739539238922/843883283598409769/summondeantendo2.gif
90	config	Make sure you have the right config file. The new config folder is at `<GameInstall>\\FactoryGame\\Configs`, ***not*** at `<GameInstall>\\Configs`. If the file is not there, make sure you've ran the game with **at least one mod installed** at least once	\N
141	nog	Nog has a Discord server! If you have any question about the mods he's working on, join here -> https://discord.gg/JjngemP9A4	\N
142	emoteanim	<a:{0}:{1}>	\N
94	smmreset	You're about to delete all your SMM profiles, so make sure you either make a backup of these files, or know the mods you had installed!\nFirst, use `Alt + F4` to close SMM. Then press `Windows Key + R`, and paste this, `%appdata%\\SatisfactoryModManager\\profiles`. Press enter, and delete all the folders in there. Now, open SMM and it should work	\N
160	fred	\N	https://cdn.discordapp.com/attachments/320955199999180802/892086083620323408/ficsitfred.png
89	consolecheats	Open `<Satisfactory Install Location>/FactoryGame/Configs/SML.cfg` with a text editor (right click -> Open with...), find enableCheatConsoleCommands and set it to true\nit should look like this: `"enableCheatConsoleCommands": true`	\N
117	multiplayer	First of all, all players involved need the exact same mods to play together\nAnd to know if a mod is multiplayer compatible : If the mod only adds recipes, items, or buildings that have no custom logic (behave just like original ones with a new model or for recipes that the mod adds) then it should work. Also, it works if the mod description says it specifically. You can also test the mod yourself, as a mod might not crash multiplayer, but it only works for the host, which you might be ok with depending on the mod	\N
165	steambranch	1) Close the game if it's open\n2) Click on the cogwheel in your steam library\n3) Go to "Properties.."\n4) On the left of this popup, go to "Betas"\n5) Now choose the desired branch in the dropdown menu	https://cdn.discordapp.com/attachments/862418592528203836/893856703513239552/SteamBranch.png
176	ask-on-sod	>sod	\N
177	rr&d	If you have any bugs, suggestions or need help with any of Refined R&D's mods you will probably get more help on their dedicated discord server.\nhttps://discord.com/invite/Vt8Rt2Vsqf	\N
178	ff	>rr&d	\N
166	fun	Fun is not allowed on this server <:goldban:894294018530349117>	\N
171	engineupdate	>engineupgrade	\N
173	rss	>kyrium	\N
179	rp	>rr&d	\N
180	factroygame	>factorygame.log	\N
181	factorygamelog	>factorygame.log	\N
182	modlist_nocheat	>qol	\N
79	calc	https://satisfactory-calculator.com/en/production-planner	\N
116	smmsml	SMM is the app that you download and interact with. It downloads files (mods and SML) to where they should go, so that you don't need to deal with them and with the mod dependencies\nSML is the mod loader it (used to load mods, now the engine does it thanks to the way mods are packaged), and provides the API for mods to interact with the game easier\nYou don't need to launch the game from SMM, it doesn't hook the game or anything	\N
133	b2	The storage service we use for satisfactory modding has gone down. We cannot do anything about this, any information will be posted in <#555428529903239178>. Please don't ask more than once	\N
102	eta	Mods that are going to be updated will be updated when they are updated. Do not ask for ETAs.	\N
105	whyborked	**Please read the following message :** https://discord.com/channels/555424930502541343/555785224873574410/838459604269662218	\N
110	tolowercase	In `%appdata%\\SatisfactoryModManager\\setting.json`, set in `selectedProfile` for every install listed there `modded`, instead of the currently saved profile	\N
140	kyrium	Kyrium has a Discord server! If you have any question about the mods he's working on, join here -> https://discord.gg/JsJ9XXWS7Q	\N
118	felix	https://ficsit-felix.netlify.app/	\N
119	modversions		https://cdn.discordapp.com/attachments/555782140533407764/846811733557379142/unknown.png
129	pirated?	https://discord.com/channels/555424930502541343/555507339969560586/853336655775662160	\N
120	newprofile		https://cdn.discordapp.com/attachments/555782140533407764/847850060087296050/unknown.png
111	crab	🦀🦀🦀 {...} 🦀🦀🦀	\N
121	feyko	<:soulless:848184791107239957><:soulless:848184791107239957><:soulless:848184791107239957><:soulless:848184791107239957><:soulless:848184791107239957><:soulless:848184791107239957>	\N
112	alpaca	<:alpaca:576075398673203210><:alpaca:576075398673203210><:alpaca:576075398673203210> {...} <:alpaca:576075398673203210><:alpaca:576075398673203210><:alpaca:576075398673203210>	\N
122	emote	<:{0}:{1}>	\N
123	emoteurl	https://cdn.discordapp.com/emojis/{...}.png	\N
107	smmconsole	Press ctrl+shift+i, then in the panel that pops up click the console tab and scroll looking for errors (they are highlighted in red). Send a screenshot when you find one	https://cdn.discordapp.com/attachments/555782140533407764/848203246282473492/unknown.png
124	tools	https://u4.satisfactorytools.com/	\N
114	translator	<https://deepl.com/translator>	\N
138	symlinkcache	In order to change the location where SMM caches the downloaded mod files you need to create a symlink for the SMM cache folder.\n1. Close SMM\n2. Create a new folder on a drive you have enough space and name it something like "SatisfactoryModManagerCache".\n3. Move the files inside `%localappdata%\\SatisfactoryModManager` to the newly created folder, and delete the original folder.\n4. Open Command Prompt as admin and run this command `mklink /D %localappdata%\\SatisfactoryModManager Some\\Where\\Else`, replacing `Some\\Where\\Else` with the path of the folder you created.\n5. Open SMM and you should now be able to download the mod	\N
148	deantendo-guide	Want to work with Deantendo for an icon or UI? Read this! https://ficsit.app/guide/5wQHZbwjYA2nJe	\N
126	scimunlocks	https://cdn.discordapp.com/attachments/555504385770258473/851846477038616586/unknown.png	\N
127	linearmotion	https://discord.gg/pnzprqWunX	\N
131	smmlinux	https://github.com/satisfactorymodding/SatisfactoryModManager/releases/latest/download/Satisfactory-Mod-Manager.AppImage	\N
149	logfilter	Press Win + R then enter: `%localappdata%\\FactoryGame\\Saved\\Config\\WindowsNoEditor\\Engine.ini` and press "OK"\nThen add the following to that file:\n```[Core.Log]\nLogStreaming=Error```	\N
139	red	Red means you shouldn't be using that mod. Either the mod is incompatible, or the author has hidden it (probably for a good reason, like having bugs) and you still have it installed	\N
150	ihaveanidea	So you've had an idea for a mod? Great! We all love new ideas, or even a new take on an existing idea.\nHere would be a list of some very common suggestions:\nhttps://ficsit.app/guide/FK8DcC44gDrFfY	\N
108	mp	First of all, all players involved need the exact same mods to play together\nAnd to know if a mod is multiplayer compatible : If the mod only adds recipes, items, or buildings that have no custom logic (behave just like original ones with a new model or for recipes that the mod adds) then it should work. Also, it works if the mod description says it specifically. You can also test the mod yourself, as a mod might not crash multiplayer, but it only works for the host, which you might be ok with depending on the mod	\N
162	verifyepic	To verify the integrity of the gamefiles please press the following buttons shown below one after the other.	https://cdn.discordapp.com/attachments/834348739539238922/892142274555813909/unknown.png
151	nokeybinds	When you think some of your modded keybinds are gone try to delete `input.ini` in `%localappdata%\\FactoryGame\\Saved\\Config\\WindowsNoEditor`	\N
145	verifysteam	To verify the integrity of the gamefiles press the button shown below	https://cdn.discordapp.com/attachments/555507339969560586/878725468071817246/unknown.png
146	sirdigby	You have Ideas or found a Bug in one of SirDigby's mods?\nThe Discord for these things can be found here:\nhttps://discord.gg/WM5KT7pVu8	\N
152	sf+	If you're experiencing problems with Satisfactory plus please remember the following things:\n- The mod is still alpha\n- The mod is not compatible with saves created before the mod was added\n- The mod might not be compatible with another mod you have installed\nIf you have more questions, suggestions or bug reports regarding Satisfactory plus or any other mod made by Kyrium you should visit his own discord as it's more likely you'll get an answer there.\nhttps://discord.gg/JsJ9XXWS7Q	\N
200	factorygame	>factorygame.log	\N
201	slow	>download	\N
202	save	you can add mods to an already existing save file\nwhen you load that file in the base game the buildings will simply disappear\nthey will also reappear in the modded game as long as you don't save in vanilla\nbut if you save in vanilla the buildings will be gone.	\N
203	saves	>save	\N
204	d4rkl0rd	D4rkl0rd has his own Discord for suggestions and bug reports for his mods, it can be found here:\nhttps://discord.gg/pnzprqWunX	\N
205	lm	>d4rkl0rd	\N
206	ss	>d4rkl0rd	\N
207	ewaf	>d4rkl0rd	\N
208	perfect-circles	>d4rkl0rd	\N
209	d4rk	>d4rkl0rd	\N
210	docs	>modding	\N
143	modding	You seem to have questions about modding.\nYou should grab the Aspiring Modder role available in <#555442202780762143> by reacting with ⚙️, read the docs carefully(<https://docs.ficsit.app/>) and if questions exist ask them in the correct channel you got through the role.	\N
199	exp	**TLDR: Mods don't work on the Experimental branch currently. Either use Early Access (if you want to play with mods), or disable the mods**\n\nThe Experimental branch now has Update 5 which breaks SML and mods. If you want to play with Update 5 you can disable mods from SMM (be warned that saving a save without the mods installed will result in all modded buildings and items disappearing). If you want to keep playing with mods, use the Early Access branch.\n\n**If you have been playing on Experimental without mods already, then changing to Early Access is not recommended since it will not be able to load or even detect your save files. If this is the case, just don't use mods\\* for the time being.**\n\n\\*See `>vanilla` for details on turning mods off.	\N
218	argtest	this {0} that {1} the other {2} this again {0} and everything {...}	\N
\.


--
-- TOC entry 3398 (class 0 OID 16397)
-- Dependencies: 213
-- Data for Name: crashes; Type: TABLE DATA; Schema: public; Owner: fred
--

COPY public.crashes (id, name, crash, response) FROM stdin;
79	steammanifest	\\[INFO\\]\\s+Invalid steam manifest (.+appmanifest_526870\\.acf)	A Steam file is corrupt: `{1}`. Open Steam, then go to that file in File Explorer and delete it. Then, verify the game files so that it will recreate that file. If Steam shows the game as not installed, install it to the same location and it will see that it is actually installed.
76	updateall	No version of SML is compatible with the other installed mods\\. Dependants: (?:[^\\s]+ \\(requires .+?\\), )*?([^\\s]+ \\(requires [\\^>=]?2\\.\\d+\\.\\d+\\))	In order to update from SML 2.2.1 to SML 3.1.1 you should disable the outdated mods when prompted, then check for updates and click "Update all" rather than updating each mod individually
77	missingalpakit	Failed to find command PackagePlugin	Some of your Alpakit files are missing. Please redownload the folder /Build/Alpakit.Automation/ from the repo
78	smart_autoconnect	Assertion failed: \\(Index >= 0\\) & \\(Index < ArrayNum\\) \\[File:d:\\\\ws\\\\sb-lowprio\\\\ue4\\\\engine\\\\source\\\\runtime\\\\core\\\\public\\\\Containers\\/Array\\.h] Assertion failed: \\(Index >= 0\\) & \\(Index < ArrayNum\\)	This may be caused by Smart's autoconnect feature. Here is the mod's creator statement on this issue : "Auto-connecting poles with belts may crash so please save the game and reload it after you built those long belts and before pushing items to there"
66	good	(smart|awesome|great|useful|good|thanks)\\s+(bot|fred)	:3
80	nospaceleft	ENOSPC: no space left on device, write	SMM caches the mods you download in `%localappdata%\\SatisfactoryModManager` (which usually is on your C: drive), so that when you switch profiles or disable mods it won't have to download the files again.\nYour C: drive is now full and SMM cannot download the mods to its cache anymore. To solve the issue you have to either clean up your C: drive, or you can create a symlink for the cache to another drive that has enough space available.\nTo learn more about the symlink option, use the command `>symlinkcache`
56	reddit	(UE4|FactoryGame)-SML-Win64-Shipping.dll'[‘‘'’`]*\\s*\\(GetLastError=1114\\)	Go to your game install dir and delete the `FactoryGame\\Binaries\\Win64` and `Engine\\Binaries\\Win64` folders. After that, verify the game files from Epic/Steam
81	nullschematic	attempt to register null schematic	You have a null schematic in your GameWorldModule
83	eperm	(EPERM: )	Sometimes SMM isn't able to read some of the files it needs to, and needs to be run as administrator to work. This should only need to be done once.
82	engineupgrade	failed\\s+to\\s+load\\s+because\\s+module\\s+.+\\s+could\\s+not\\s+be\\s+loaded\\.	>engineupgrade
86	engineupgrade2	\\?GPixelFormats@	>engineupgrade
84	nullrecipe	^(?:\\[20.*)?(?:Attempt|Fatal) .* '.*\\.([^/]+)_C' registered by .* references invalid NULL Recipe	Your {1} schematic references a null recipe (`None`) in the unlocks list
20	buildforshipping	Missing UE4Game binary.	You need to also build for Shipping before using Alpakit
90	riderlink	"('RiderLink'\\s*failed\\s*to\\s*load)|(The\\s*following\\s*modules\\s*are\\s*missing\\s*or\\s*built\\s*with\\s*a\\s*different\\s*engine\\s*version:\\s*RD\\s*RiderLink)"	Somehow RiderLink isn't installed (we don't know why this happens yet). To fix this, you can reinstall it in Rider's settings menu like this: https://cdn.discordapp.com/attachments/601030071221878784/894346572765212742/unknown.png
23	alpakitautomationdll	Failed to load script DLL	Go to the mentioned file, right click on it, hit Properties and tick the box at the bottom to unlock the file
92	d3d	GPU crashed or D3D device removed	Please force the use of DirectX11 with your game by adding the -d3d11 argument to your game
25	exprenderer	UE4-FactoryGame-Win64-Shipping.dll!AFGBuildableConveyorBase::Factory_Tick()	This crash may be caused by the Experimental Conveyor Renderer. Please turn it off in your Graphics setting and see if the crash goes away. You may experience a significant performance drop when doing so
89	mehbot	(\\s|^)(meh|average|ok|weird|mediocre)\\s*bot	:|
93	dependentnodebfired	!DependentNode->bFired\\s*\\[	We aren't quite sure what causes this, but if you get this while opening the game, try not to go into another window while it opens. Additionally, as with most UE4 errors, try verifying files.
97	fredsimpsforfeyko	good\\sfeyko	ONLY I AM ALLOWED TO PRAISE MY GOD
47	moremilestonesmp	FactoryGame_FactoryGame_Win64_Shipping!AFGItemRegrowSubsystem::AddPickup	More Milestones doesn't work in multiplayer currently
49	sml300mp	Assertion failed: GameState	Multiplayer doesn't work with SML 3.0.0. It was fixed in SML 3.1.0, but it only works with game version >=151773 which is only available on Experimental currently
52	notbuilt	FactoryGame\\s+could\\s+not\\s+be\\s+compiled.\\s+Try\\s+rebuilding\\s+from\\s+source\\s+manually	You did not build the project in Visual Studio. Please go back to the Project Setup section of the docs and do not skip steps nor do more than is asked
54	.netmissing	Install a version of .NET Framework SDK at	Your .NET Framework install is either missing or oudated. Please download and install the latest one from https://dotnet.microsoft.com/download/visual-studio-sdks. Make sure to download the .NET **Framework**SDK
55	noautomationtool	UATHelper: Package Mod Task (Windows): RunUAT.bat ERROR: Visual studio and/or AutomationTool.csproj was not found, nor was Engine\\Binaries\\DotNET\\AutomationTool.exe. Can't run the automation tool.	Open your .sln with Visual Studio/Rider and build the project for Shipping
64	tolowercase	c\\.toLowerCase is not a function	>tolowercase
69	fixit	Can we (fix\\s*it|ficsit)\\s*?	Yes we can!
70	oldproject	ERROR: Cannot find game version file	Your project is outdated. Please update it
71	needcompile	Module\\s+[‘‘'’`]*FactoryGame[‘‘'’`]*\\s+could\\s+not\\s+be\\s+found	Please open your .sln with Visual Studio/Rider and build the project for both Development Editor and Shipping
72	oldengine	The\\s+name[‘‘'’`]*bOverrideAppNameForSharedBuild[‘‘'’`]*\\s+does\\s+not\\s+exist\\s+in\\s+the\\s+current\\s+context	Please update your engine to the latest from <https://github.com/SatisfactoryModdingUE/UnrealEngine/releases>
74	modupdates	Mod updates are available	You have mod updates available. If you are having issues with outdated mods, make sure to click Update All rather than updating each mod individually.
53	dataja	(can I ask( you)*|I have) a question (about (?:\\w+\\s?){0,2})?.{0,5}$	https://dontasktoask.com/
94	author	who (created|made|wrote) (fred|the bot)	I was created by 3 amazing people\n<https://github.com/Feyko/FICSIT-Fred/graphs/contributors>
68	flip	\\(╯°□°\\)╯︵ ┻━┻	┬─┬ ノ( ゜-゜ノ)
\.


--
-- TOC entry 3400 (class 0 OID 16403)
-- Dependencies: 215
-- Data for Name: dialogflow; Type: TABLE DATA; Schema: public; Owner: fred
--

COPY public.dialogflow (id, intent_id, data, response, has_followup) FROM stdin;
1	613eaabc-035c-4474-8a3c-2ae24a59015e	{"platform": "Steam"}	>factorygame.log	f
2	613eaabc-035c-4474-8a3c-2ae24a59015e	{"platform": "Epic"}	>factorygame.log	f
3	711ec617-90e7-498a-b169-96ea99f70482	{"game_version": ""}	\N	t
4	711ec617-90e7-498a-b169-96ea99f70482	{"game_version": "early access"}	Try launching from the exe in the game install dir	f
6	9af5992c-7a9a-4622-bbae-0ab333a68dd5	{"game_version": "early access"}	Try launching from the exe in the game install dir	f
10	613eaabc-035c-4474-8a3c-2ae24a59015e	{"platform": "Cracked"}	<@&555431049300017162>	f
11	b9f3be13-3854-4a77-9847-6cefbd33ec05	{"platform": "Epic"}	>factorygame.log	f
12	b9f3be13-3854-4a77-9847-6cefbd33ec05	{"platform": "Steam"}	>factorygame.log	f
13	b9f3be13-3854-4a77-9847-6cefbd33ec05	{"platform": "Cracked"}	<@&555431049300017162>	f
14	b9f3be13-3854-4a77-9847-6cefbd33ec05	{"platform": ""}	\N	t
5	711ec617-90e7-498a-b169-96ea99f70482	{"game_version": "both"}	>steamexp	f
7	9af5992c-7a9a-4622-bbae-0ab333a68dd5	{"game_version": "experimental"}	>steamexp	f
8	9af5992c-7a9a-4622-bbae-0ab333a68dd5	{"game_version": "both"}	>steamexp	f
15	711ec617-90e7-498a-b169-96ea99f70482	{"game_version": "experimental"}	>steamexp	f
9	09fd954b-5038-43aa-a8d1-c5f10d6749d6	\N	>kronos	f
16	64fcb215-d913-4825-9bd2-59c96684a6ee	\N	>steamexp	f
18	b55e15a8-8b45-432f-8ae5-dc361b3f8ee4	\N	>exp	f
\.


--
-- TOC entry 3401 (class 0 OID 16408)
-- Dependencies: 216
-- Data for Name: dialogflow_channels; Type: TABLE DATA; Schema: public; Owner: fred
--

COPY public.dialogflow_channels (id, channel_id) FROM stdin;
1	555516979260293132
2	555782140533407764
3	320955199999180802
\.


--
-- TOC entry 3403 (class 0 OID 16412)
-- Dependencies: 218
-- Data for Name: dialogflow_exception_roles; Type: TABLE DATA; Schema: public; Owner: fred
--

COPY public.dialogflow_exception_roles (id, role_id) FROM stdin;
1	829446270300586015
2	829443769786564638
3	829446814687166484
4	836570514355912704
\.


--
-- TOC entry 3406 (class 0 OID 16417)
-- Dependencies: 221
-- Data for Name: media_only_channels; Type: TABLE DATA; Schema: public; Owner: fred
--

COPY public.media_only_channels (id, channel_id) FROM stdin;
1	696718959193489438
2	562121682538594314
7	1283104993875857511
8	854810398858412044
9	1293357175644880926
\.


--
-- TOC entry 3408 (class 0 OID 16421)
-- Dependencies: 223
-- Data for Name: miscellaneous; Type: TABLE DATA; Schema: public; Owner: fred
--

COPY public.miscellaneous (id, key, value) FROM stdin;
11	filter_channel	320955199999180802
12	mod_channel	320955199999180802
13	githook_channel	360826726055411723
14	prefix	"?"
8	levelling_state	true
4	rank_value_multiplier	1.3
5	xp_gain_value	10
3	base_rank_value	300
6	xp_gain_delay	20
1	welcome_message	"Welcome, new person ! I am sorry to DM you as soon you join, but please read on, it is important :\\nYou (just like anyone else who joins this server) have been muted for 10 minutes to give you the time to read this message, the rules, the faq and potentially the channels if you have a question that wasn't answered in the faq\\n\\nPlease, do make use of those 5 minutes and read everything that I just mentioned\\nIf you ever have a question unanswered by the faq, please first scroll through appropriate channels a bit and/or use the Discord search function (top right on Desktop) to search for questions close to yours\\n\\nBelow this message will be any important info that we really really want you to know (If there is no message then there is nothing major happening currently)"
16	is_running	true
17	base_level_value	300
18	level_value_multiplier	1.3
2	latest_info	""
7	main_guild_id	854423652262215710
20	error_channel	1269746804501647412
19	migration_rev	2
\.


--
-- TOC entry 3410 (class 0 OID 16427)
-- Dependencies: 225
-- Data for Name: rank_roles; Type: TABLE DATA; Schema: public; Owner: fred
--

COPY public.rank_roles (id, rank, role_id) FROM stdin;
\.


--
-- TOC entry 3412 (class 0 OID 16431)
-- Dependencies: 227
-- Data for Name: reserved_commands; Type: TABLE DATA; Schema: public; Owner: fred
--

COPY public.reserved_commands (id, name) FROM stdin;
1	mod (name)
2	help
3	docsearch
4	add response
5	remove response
6	add crash
7	remove crash
8	add media only
9	remove media only
10	add command
11	remove command
12	prefix
13	engineers
14	moderators
15	githook
16	members
17	growth
\.


--
-- TOC entry 3414 (class 0 OID 16437)
-- Dependencies: 229
-- Data for Name: role_perms; Type: TABLE DATA; Schema: public; Owner: fred
--

COPY public.role_perms (id, role_id, perm_lvl, role_name) FROM stdin;
1	555432362498850817	1	Trainee Modder
2	829455392621985873	2	Regular
3	829446002209194074	3	Helpful
4	849612375858741259	3	Documentation Contributor
5	851186120301084682	3	Tool Developer
6	555432397395722260	3	Legacy Engineer
7	858084420815421490	3	Master Modder
8	855582239277187082	4	Certified Engineer
9	571819240609284096	5	Infrastructure Engineer
10	740318257164058654	5	Critical Engineer
11	555431049300017162	6	Moderator
12	555426814177181701	7	Server Admin
13	590597379569352714	7	Admin
14	854455256569479220	6	the powers that be
\.


--
-- TOC entry 3417 (class 0 OID 16444)
-- Dependencies: 232
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: fred
--

COPY public.users (id, user_id, full_name, message_count, xp_count, xp_multiplier, role_xp_multiplier, rank, rank_role_id, accepts_dms) FROM stdin;
1	227473074616795137	Feyko#7953	57156	138424	1	1	24	\N	t
22693	147821698379546625	\N	7	50	1	1	0	\N	t
22692	506192269557366805	\N	244	450	1	1	2	\N	t
\.


--
-- TOC entry 3434 (class 0 OID 0)
-- Dependencies: 210
-- Name: action_colours_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fred
--

SELECT pg_catalog.setval('public.action_colours_id_seq', 9, true);


--
-- TOC entry 3435 (class 0 OID 0)
-- Dependencies: 212
-- Name: commands_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fred
--

SELECT pg_catalog.setval('public.commands_id_seq', 219, true);


--
-- TOC entry 3436 (class 0 OID 0)
-- Dependencies: 214
-- Name: crashes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fred
--

SELECT pg_catalog.setval('public.crashes_id_seq', 98, true);


--
-- TOC entry 3437 (class 0 OID 0)
-- Dependencies: 217
-- Name: dialogflow_channels_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fred
--

SELECT pg_catalog.setval('public.dialogflow_channels_id_seq', 3, true);


--
-- TOC entry 3438 (class 0 OID 0)
-- Dependencies: 219
-- Name: dialogflow_exception_roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fred
--

SELECT pg_catalog.setval('public.dialogflow_exception_roles_id_seq', 1, true);


--
-- TOC entry 3439 (class 0 OID 0)
-- Dependencies: 220
-- Name: dialogflow_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fred
--

SELECT pg_catalog.setval('public.dialogflow_id_seq', 18, true);


--
-- TOC entry 3440 (class 0 OID 0)
-- Dependencies: 222
-- Name: media_only_channels_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fred
--

SELECT pg_catalog.setval('public.media_only_channels_id_seq', 9, true);


--
-- TOC entry 3441 (class 0 OID 0)
-- Dependencies: 224
-- Name: miscellaneous_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fred
--

SELECT pg_catalog.setval('public.miscellaneous_id_seq', 20, true);


--
-- TOC entry 3442 (class 0 OID 0)
-- Dependencies: 226
-- Name: rank_roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fred
--

SELECT pg_catalog.setval('public.rank_roles_id_seq', 1, false);


--
-- TOC entry 3443 (class 0 OID 0)
-- Dependencies: 228
-- Name: reserved_commands_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fred
--

SELECT pg_catalog.setval('public.reserved_commands_id_seq', 17, true);


--
-- TOC entry 3444 (class 0 OID 0)
-- Dependencies: 230
-- Name: role_perms_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fred
--

SELECT pg_catalog.setval('public.role_perms_id_seq', 13, true);


--
-- TOC entry 3445 (class 0 OID 0)
-- Dependencies: 231
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fred
--

SELECT pg_catalog.setval('public.users_id_seq', 22693, true);


--
-- TOC entry 3232 (class 2606 OID 16462)
-- Name: action_colours action_colours_pkey; Type: CONSTRAINT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.action_colours
    ADD CONSTRAINT action_colours_pkey PRIMARY KEY (id);


--
-- TOC entry 3234 (class 2606 OID 16464)
-- Name: commands commands_pkey; Type: CONSTRAINT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.commands
    ADD CONSTRAINT commands_pkey PRIMARY KEY (id);


--
-- TOC entry 3236 (class 2606 OID 16466)
-- Name: crashes crashes_pkey; Type: CONSTRAINT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.crashes
    ADD CONSTRAINT crashes_pkey PRIMARY KEY (id);


--
-- TOC entry 3240 (class 2606 OID 16468)
-- Name: dialogflow_channels dialogflow_channels_pkey; Type: CONSTRAINT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.dialogflow_channels
    ADD CONSTRAINT dialogflow_channels_pkey PRIMARY KEY (id);


--
-- TOC entry 3242 (class 2606 OID 16470)
-- Name: dialogflow_exception_roles dialogflow_exception_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.dialogflow_exception_roles
    ADD CONSTRAINT dialogflow_exception_roles_pkey PRIMARY KEY (id);


--
-- TOC entry 3238 (class 2606 OID 16472)
-- Name: dialogflow dialogflow_pkey; Type: CONSTRAINT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.dialogflow
    ADD CONSTRAINT dialogflow_pkey PRIMARY KEY (id);


--
-- TOC entry 3244 (class 2606 OID 16474)
-- Name: media_only_channels media_only_channels_pkey; Type: CONSTRAINT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.media_only_channels
    ADD CONSTRAINT media_only_channels_pkey PRIMARY KEY (id);


--
-- TOC entry 3246 (class 2606 OID 16476)
-- Name: miscellaneous miscellaneous_pkey; Type: CONSTRAINT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.miscellaneous
    ADD CONSTRAINT miscellaneous_pkey PRIMARY KEY (id);


--
-- TOC entry 3248 (class 2606 OID 16478)
-- Name: rank_roles rank_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.rank_roles
    ADD CONSTRAINT rank_roles_pkey PRIMARY KEY (id);


--
-- TOC entry 3250 (class 2606 OID 16480)
-- Name: reserved_commands reserved_commands_pkey; Type: CONSTRAINT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.reserved_commands
    ADD CONSTRAINT reserved_commands_pkey PRIMARY KEY (id);


--
-- TOC entry 3252 (class 2606 OID 16482)
-- Name: role_perms role_perms_pkey; Type: CONSTRAINT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.role_perms
    ADD CONSTRAINT role_perms_pkey PRIMARY KEY (id);


--
-- TOC entry 3254 (class 2606 OID 16484)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: fred
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


-- Completed on 2025-02-16 19:07:30 UTC

--
-- PostgreSQL database dump complete
--

