import os
import subprocess
import asyncio
import pytesseract
from PIL import Image

import discord
from discord.ext import commands

from assets import list_funcs, otp_assets, image_assets, discord_funcs
from assets.discord_funcs import get_avatar_url


class ImageProcessing(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        response = subprocess.run(["tesseract", "--list-langs"], stdout=subprocess.PIPE)
        self.tesseract_languages = response.stdout.decode("utf-8").split("\n")[1:-1]

        self.delete_path = "images/delete.png"
        self.spidey_path = "images/spidey_point.png"
        try:
            os.mkdir("storage")
        except FileExistsError:
            pass

    @commands.command(name="ocrlangs", aliases=["ocrlang", "ocrlangslist", "ocrlanglist"])
    async def ocrlangs(self, ctx):
        """
        Lists all the languages that can be used with the OCR command.
        """

        chunked_list = list(list_funcs.chunks(self.tesseract_languages, 25))
        try:
            await ctx.author.send("List of language codes for the OCR command:")
        except discord.Forbidden:
            return await ctx.reply('Could not send message to you. Please enable PMs and try again.')
        except Exception as e:
            self.bot.logger.log_error(e, "langcodes")
        n = 0
        for top_list in chunked_list:
            string = ""
            for x in top_list:
                string += f"\n{x}"
                n += 1
            await asyncio.sleep(1)
            await ctx.author.send(f"```{string}```")
        await ctx.author.send(f'Total: {n} entries.')

    @commands.command(name="ocr", aliases=["ocrtext", "ocrtexts"])
    async def ocr(self, ctx, language_code=None, image_url=None):
        """Recognizes text characters in an image.
        Use the `ocrlangs` command to see a list of language codes."""

        if not image_url and not ctx.message.attachments:
            return await ctx.send("Please provide an image to OCR.")
        if not language_code:
            language_code = "eng" if "eng" in self.tesseract_languages else self.tesseract_languages[0]
        else:
            # Check if passed language code is valid
            if language_code.lower() not in [x.lower() for x in self.tesseract_languages]:
                return await ctx.send(f"Language code `{language_code}` not found. "
                                      f"Use the `ocrlangs` command to see a list of language codes.")
        if not image_url:
            image_url = ctx.message.attachments[0].url

        otp = otp_assets.generate_otp(5)
        file_path = f"storage/ocr{otp}.png"
        await image_assets.save_image(image_url, file_path)
        await ctx.trigger_typing()
        text = str(pytesseract.image_to_string(Image.open(file_path), lang=language_code.lower())).strip("\n")
        embed = discord.Embed(title="OCR Result", description=f"```"
                                                              f"{text[:2000] if text else 'No text was recognized :('}"
                                                              f"```",
                              color=discord_funcs.get_color(ctx.author))
        embed.set_footer(text=f"Language used: {language_code}")
        await ctx.send(embed=embed)
        os.remove(file_path)

    @commands.command(name="delete", aliases=["deleteuser"])
    async def delete_user(self, ctx, *, member: discord.Member = None):
        """Delete the user. Show no mercy."""
        random_number = otp_assets.generate_otp(5)
        if member is None:
            member = ctx.author
        await ctx.trigger_typing()
        pfp_path = await image_assets.save_image(get_avatar_url(member), f"storage/pfp{member.id}.png")
        image_assets.resize_image(pfp_path, (400, 400))
        image_assets.superimpose_image(pfp_path, self.delete_path, offset=(360, 320),
                                       final_path=f"storage/delete{random_number}.png")
        file = discord.File(f"./storage/delete{random_number}.png", filename=f"delete{random_number}.png")
        embed = discord.Embed(title=f"{member.display_name} has been **deleted**!",
                              color=discord_funcs.get_color(member))
        embed.set_image(url=f"attachment://delete{random_number}.png")
        if member != ctx.author:
            embed.set_footer(text=f"{member.display_name} was deleted by {ctx.author.display_name} :(",
                             icon_url=get_avatar_url(ctx.author))
        else:
            embed.set_footer(text=f"{ctx.author.display_name} deleted themselves :(", icon_url=get_avatar_url(ctx.author))
        await ctx.reply(file=file, embed=embed)
        os.remove(f"./storage/delete{random_number}.png")
        os.remove(f"./storage/pfp{member.id}.png")

    @commands.command(name="point", aliases=["spideypoint", "spiderman"])
    async def point(self, ctx, member1: discord.Member, member2: discord.Member = None):
        """Make a spidey-point meme with the given members."""
        if member2 is None:
            member2 = ctx.author
        random_number = otp_assets.generate_otp(5)
        await ctx.trigger_typing()
        pfp_path1 = await image_assets.save_image(get_avatar_url(member1), f"storage/pfp{member1.id}.png")
        pfp_path2 = await image_assets.save_image(get_avatar_url(member2), f"storage/pfp{member2.id}.png")
        image_assets.resize_image(pfp_path1, (200, 200))
        image_assets.resize_image(pfp_path2, (200, 200))
        image_assets.superimpose_image(pfp_path1, self.spidey_path, offset=(480, 145),
                                       final_path=f"storage/spidey{random_number}.png")
        image_assets.superimpose_image(pfp_path2, f"storage/spidey{random_number}.png", offset=(1415, 175),
                                       final_path=f"storage/spidey{random_number}.png")
        file = discord.File(f"./storage/spidey{random_number}.png", filename=f"spidey{random_number}.png")
        if member1 != member2:
            embed = discord.Embed(title=f"{member1.display_name} and {member2.display_name} point at each other.",
                                  color=discord_funcs.get_color(ctx.author))
        else:
            embed = discord.Embed(title=f"{member1.display_name} points at themselves. Is this the multiverse?",
                                  color=discord_funcs.get_color(member2))
        embed.set_image(url=f"attachment://spidey{random_number}.png")
        embed.set_footer(text=f"{ctx.author.display_name} wanted this.", icon_url=get_avatar_url(ctx.author))
        await ctx.reply(file=file, embed=embed)
        try:
            os.remove(f"./storage/spidey{random_number}.png")
            os.remove(f"./storage/pfp{member1.id}.png")
            os.remove(f"./storage/pfp{member2.id}.png")
        except FileNotFoundError:
            pass


def setup(bot):
    bot.add_cog(ImageProcessing(bot))