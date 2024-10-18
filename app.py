from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from colorama import *
from datetime import UTC, datetime, timedelta
from fake_useragent import FakeUserAgent
from faker import Faker
from telethon.errors import (
    AuthKeyUnregisteredError,
    UserDeactivatedError,
    UserDeactivatedBanError,
    UnauthorizedError
)
from telethon.functions import messages
from telethon.sync import TelegramClient
from telethon.types import AppWebViewResultUrl
from urllib.parse import parse_qs, unquote
import asyncio, json, os, sys

class Timefarm:
    def __init__(self) -> None:
        config = json.load(open('config.json', 'r'))
        self.api_id = int(config['api_id'])
        self.api_hash = config['api_hash']
        self.faker = Faker()
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Host': 'tg-bot-tap.laborx.io',
            'Origin': 'https://timefarm.app',
            'Pragma': 'no-cache',
            'Priority': 'u=3, i',
            'Referer': 'https://timefarm.app/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'User-Agent': FakeUserAgent().random
        }

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_timestamp(self, message):
        print(
            f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{message}",
            flush=True
        )

    async def generate_query(self, session: str):
        try:
            client = TelegramClient(session=f'sessions/{session}', api_id=self.api_id, api_hash=self.api_hash)
            try:
                if not client.is_connected():
                    await client.connect()
            except (AuthKeyUnregisteredError, UnauthorizedError, UserDeactivatedError, UserDeactivatedBanError) as e:
                raise e

            await client(messages.StartBotRequest(
                peer = 'TimeFarmCryptoBot',
                bot = await client.get_input_entity('TimeFarmCryptoBot'),
                start_param = 'LnDO5pMtlVk6eMVL'
            ))
            webapp_response: AppWebViewResultUrl = await client(messages.RequestWebViewRequest(
                peer = 'TimeFarmCryptoBot',
                bot = await client.get_input_entity('TimeFarmCryptoBot'),
                platform = 'ios',
                url = 'https://tg-bot-tap.laborx.io/'
            ))
            query = unquote(string=webapp_response.url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

            if client.is_connected():
                await client.disconnect()

            return query
        except Exception as e:
            await client.disconnect()
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {session} Unexpected Error While Generating Query With Telethon: {str(e)} ]{Style.RESET_ALL}")
            return None

    async def generate_queries(self, sessions):
        tasks = [self.generate_query(session) for session in sessions]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]

    async def generate_token(self, query: str):
        url = 'https://tg-bot-tap.laborx.io/api/v1/auth/validate-init/v2'
        data = json.dumps({'initData':query,'platform':'ios'})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    user_data = json.loads(parse_qs(query)['user'][0])
                    first_name = user_data['first_name'] or self.faker.first_name()
                    return (await response.json(), first_name)
        except (Exception, ClientResponseError) as e:
            self.print_timestamp(
                f"{Fore.YELLOW + Style.BRIGHT}[ Failed To Process {query} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}"
            )
            return None

    async def generate_tokens(self, queries):
        tasks = [self.generate_token(query) for query in queries]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]

    async def complete_onboarding_me(self, token: str):
        url = 'https://tg-bot-tap.laborx.io/api/v1/me/onboarding/complete'
        data = json.dumps({})
        headers = {
            **self.headers,
            'Authorization': f"Bearer {token}",
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError):
            return False

    async def info_farming(self, token: str):
        url = 'https://tg-bot-tap.laborx.io/api/v1/farming/info'
        headers = {
            **self.headers,
            'Authorization': f"Bearer {token}"
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    return await response.json()
        except ClientResponseError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Info Farming: {str(e)} ]{Style.RESET_ALL}")
            return None
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Info Farming: {str(e)} ]{Style.RESET_ALL}")
            return None

    async def start_farming(self, token: str):
        url = 'https://tg-bot-tap.laborx.io/api/v1/farming/start'
        data = json.dumps({})
        headers = {
            **self.headers,
            'Authorization': f"Bearer {token}",
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    if response.status == 403:
                        error_start_farming = await response.json()
                        if error_start_farming['error']['message'] == 'Farming already started':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farming Already Started ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    start_farming = await response.json()
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Farming Started And Can Be Claim At {(datetime.strptime(start_farming['activeFarmingStartedAt'], '%Y-%m-%dT%H:%M:%S.%fZ') + timedelta(seconds=start_farming['farmingDurationInSec'])).astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}")
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Start Farming: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Start Farming: {str(e)} ]{Style.RESET_ALL}")

    async def finish_farming(self, token: str, farming_reward: int):
        url = 'https://tg-bot-tap.laborx.io/api/v1/farming/finish'
        data = json.dumps({})
        headers = {
            **self.headers,
            'Authorization': f"Bearer {token}",
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    if response.status == 403:
                        error_finish_farming = await response.json()
                        if error_finish_farming['error']['message'] == 'Too early to finish farming':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Too Early To Finish Farming ]{Style.RESET_ALL}")
                        elif error_finish_farming['error']['message'] == 'Farming didn\'t start':
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farming Didn\'t Start ]{Style.RESET_ALL}")
                            return await self.start_farming(token=token)
                    response.raise_for_status()
                    self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {farming_reward} From Farming ]{Style.RESET_ALL}")
                    return await self.start_farming(token=token)
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Finish Farming: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Finish Farming: {str(e)} ]{Style.RESET_ALL}")

    async def claim_referral_balance(self, token: str, available_balance: int):
        url = 'https://tg-bot-tap.laborx.io/api/v1/balance/referral/claim'
        data = json.dumps({})
        headers = {
            **self.headers,
            'Authorization': f"Bearer {token}",
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    if response.status == 403:
                        error_claim_referral = await response.json()
                        if error_claim_referral['error']['message'] == 'Nothing to claim':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Nothing To Claim From Referral ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {available_balance} From Referral ]{Style.RESET_ALL}")
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Referral: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Referral: {str(e)} ]{Style.RESET_ALL}")

    async def tasks(self, token: str):
        url = 'https://tg-bot-tap.laborx.io/api/v1/tasks'
        headers = {
            **self.headers,
            'Authorization': f"Bearer {token}"
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    tasks = await response.json()
                    for task in tasks:
                        if task['type'] != 'ADSGRAM' and task['type'] != 'TADS':
                            if not 'submission' in task or task['submission']['status'] == 'REJECTED':
                                await self.submissions_tasks(token=token, task_id=task['id'], task_title=task['title'], task_reward=task['reward'])
                            elif task['submission']['status'] == 'COMPLETED':
                                await self.claims_tasks(token=token, task_id=task['id'], task_title=task['title'], task_reward=task['submission']['reward'])
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Tasks: {str(e)} ]{Style.RESET_ALL}")

    async def submissions_tasks(self, token: str, task_id: str, task_title: str, task_reward: int):
        url = f'https://tg-bot-tap.laborx.io/api/v1/tasks/{task_id}/submissions'
        data = json.dumps({})
        headers = {
            **self.headers,
            'Authorization': f"Bearer {token}",
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    if response.status in [400, 403]:
                        error_submissions_tasks = await response.json()
                        if error_submissions_tasks['error']['message'] == 'Already submitted':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ {task_title} Already Submitted ]{Style.RESET_ALL}")
                        elif error_submissions_tasks['error']['message'] == 'Forbidden':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ API Response Got Forbidden While Submissions {task_title} ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    submissions_tasks = await response.json()
                    if submissions_tasks['result']['status'] == 'COMPLETED':
                        return await self.claims_tasks(token=token, task_id=task_id, task_title=task_title, task_reward=task_reward)
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Submissions Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Submissions Tasks: {str(e)} ]{Style.RESET_ALL}")

    async def claims_tasks(self, token: str, task_id: str, task_title: str, task_reward: int):
        url = f'https://tg-bot-tap.laborx.io/api/v1/tasks/{task_id}/claims'
        data = json.dumps({})
        headers = {
            **self.headers,
            'Authorization': f"Bearer {token}",
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    if response.status == 400:
                        error_claim_tasks = await response.json()
                        if error_claim_tasks['error']['message'] == 'Failed to claim reward':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Failed To Claim {task_title} ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {task_reward} From {task_title} ]{Style.RESET_ALL}")
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claims Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claims Tasks: {str(e)} ]{Style.RESET_ALL}")

    async def upgrade_level(self, token: str):
        url = 'https://tg-bot-tap.laborx.io/api/v1/me/level/upgrade'
        data = json.dumps({})
        headers = {
            **self.headers,
            'Authorization': f"Bearer {token}",
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    if response.status == 403:
                        error_upgrade_level = await response.json()
                        if error_upgrade_level['error']['message'] == 'Not enough balance':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Not Enough Balance To Upgrade Level ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    upgrade_level = await response.json()
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Successfully Upgrade Level To {upgrade_level['level']} ]{Style.RESET_ALL}")
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Upgrade Level: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Upgrade Level: {str(e)} ]{Style.RESET_ALL}")

    async def answer(self):
        url = 'https://raw.githubusercontent.com/Shyzg/answer/refs/heads/main/answer.json'
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, ssl=False) as response:
                    response.raise_for_status()
                    return json.loads(await response.text())
        except (Exception, ClientResponseError):
            return None

    async def get_daily_questions(self, token: str):
        url = 'https://tg-bot-tap.laborx.io/api/v1/daily-questions'
        headers = {
            **self.headers,
            'Authorization': f"Bearer {token}"
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers, ssl=False) as response:
                    if response.status == 403:
                        error_daily_questions = await response.json()
                        if error_daily_questions['error']['message'] == 'There are no daily question':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ There Are No Daily Question ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    daily_questions = await response.json()
                    if 'answer' in daily_questions:
                        if daily_questions['answer']['isCorrect']:
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Daily Questions Already Answered Correct ]{Style.RESET_ALL}")
                    answer = await self.answer()
                    if answer is not None:
                        if datetime.fromtimestamp(answer['expires']).astimezone().timestamp() > datetime.now().astimezone().timestamp():
                            return await self.post_daily_questions(token=token, answer=answer['timefarm'], reward=daily_questions['reward'])
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Daily Questions: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Daily Questions: {str(e)} ]{Style.RESET_ALL}")

    async def post_daily_questions(self, token: str, answer: str, reward: int):
        url = 'https://tg-bot-tap.laborx.io/api/v1/daily-questions'
        data = json.dumps({'answer':answer})
        headers = {
            **self.headers,
            'Authorization': f"Bearer {token}",
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    daily_questions = await response.json()
                    if daily_questions['isCorrect']:
                        return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {reward} From Daily Questions ]{Style.RESET_ALL}")
        except ClientResponseError as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Post Daily Questions: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Post Daily Questions: {str(e)} ]{Style.RESET_ALL}")

    async def main(self):
        while True:
            try:
                sessions = [file for file in os.listdir('sessions/') if file.endswith('.session')]
                if not sessions:
                    return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ No Session Files Found In The Folder! Please Make Sure There Are '*.session' Files In The Folder. ]{Style.RESET_ALL}")
                queries = await self.generate_queries(sessions=sessions)
                accounts = await self.generate_tokens(queries=queries)
                restart_times = []
                total_balance = 0

                for (account, first_name) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Home ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                    )
                    await self.complete_onboarding_me(token=account['token'])
                    self.print_timestamp(
                        f"{Fore.BLUE + Style.BRIGHT}[ Balance {account['balanceInfo']['balance']} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}[ Clocks Level {account['info']['level']} ]{Style.RESET_ALL}"
                    )
                    info_farming = await self.info_farming(token=account['token'])
                    if info_farming is not None:
                        if 'activeFarmingStartedAt' in info_farming:
                            end_farm = (datetime.strptime(info_farming['activeFarmingStartedAt'], "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(seconds=info_farming['farmingDurationInSec'])).replace(tzinfo=UTC).astimezone()
                            if datetime.now().astimezone() >= end_farm:
                                await self.finish_farming(token=account['token'], farming_reward=info_farming['farmingReward'])
                            else:
                                restart_times.append(end_farm.timestamp())
                                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farming Can Be Claim At {end_farm.strftime('%x %X %Z')} ]{Style.RESET_ALL}")
                        else:
                            await self.start_farming(token=account['token'])
                    if 'availableBalance' in account['balanceInfo']['referral'] and account['balanceInfo']['referral']['availableBalance'] != 0:
                        await self.claim_referral_balance(token=account['token'], available_balance=account['balanceInfo']['referral']['availableBalance'])
                    await self.upgrade_level(token=account['token'])
                    await self.get_daily_questions(token=account['token'])

                for (account, first_name) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Tasks ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                    )
                    await self.tasks(token=account['token'])

                for (account, first_name) in accounts:
                    total_balance += account['balanceInfo']['balance']

                if restart_times:
                    wait_times = [farming - datetime.now().astimezone().timestamp() for farming in restart_times if farming > datetime.now().astimezone().timestamp()]
                    if wait_times:
                        sleep_time = min(wait_times)
                    else:
                        sleep_time = 15 * 60
                else:
                    sleep_time = 15 * 60

                self.print_timestamp(
                    f"{Fore.CYAN + Style.BRIGHT}[ Total Account {len(accounts)} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT}[ Total Balance {total_balance} ]{Style.RESET_ALL}"
                )
                self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Restarting At {(datetime.now().astimezone() + timedelta(seconds=sleep_time)).strftime('%x %X %Z')} ]{Style.RESET_ALL}")

                await asyncio.sleep(sleep_time)
                self.clear_terminal()
            except Exception as e:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
                continue

if __name__ == '__main__':
    try:
        if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        init(autoreset=True)
        timefarm = Timefarm()
        asyncio.run(timefarm.main())
    except (ValueError, IndexError, FileNotFoundError) as e:
        timefarm.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
    except KeyboardInterrupt:
        sys.exit(0)