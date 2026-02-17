using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.Versioning;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using AspNetCoreGeneratedDocument;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.ApplicationParts;
using Microsoft.AspNetCore.Mvc.Razor;
using Microsoft.AspNetCore.Mvc.Razor.Internal;
using Microsoft.AspNetCore.Mvc.Razor.TagHelpers;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.AspNetCore.Mvc.TagHelpers;
using Microsoft.AspNetCore.Mvc.ViewFeatures;
using Microsoft.AspNetCore.Razor.Hosting;
using Microsoft.AspNetCore.Razor.Runtime.TagHelpers;
using Microsoft.AspNetCore.Razor.TagHelpers;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using WebGame.Models;
using WebGame.Services;

[assembly: CompilationRelaxations(8)]
[assembly: RuntimeCompatibility(WrapNonExceptionThrows = true)]
[assembly: Debuggable(DebuggableAttribute.DebuggingModes.IgnoreSymbolStoreSequencePoints)]
[assembly: TargetFramework(".NETCoreApp,Version=v8.0", FrameworkDisplayName = ".NET 8.0")]
[assembly: AssemblyCompany("project")]
[assembly: AssemblyConfiguration("Release")]
[assembly: AssemblyFileVersion("1.0.0.0")]
[assembly: AssemblyInformationalVersion("1.0.0+7fcb9fe4065afac898d13b660eef0830e4e029d5")]
[assembly: AssemblyProduct("project")]
[assembly: AssemblyTitle("project")]
[assembly: ProvideApplicationPartFactory("Microsoft.AspNetCore.Mvc.ApplicationParts.ConsolidatedAssemblyApplicationPartFactory, Microsoft.AspNetCore.Mvc.Razor")]
[assembly: RazorCompiledItem(typeof(Views_Home_Index), "mvc.1.0.view", "/Views/Home/Index.cshtml")]
[assembly: RazorCompiledItem(typeof(Views_Shared__Layout), "mvc.1.0.view", "/Views/Shared/_Layout.cshtml")]
[assembly: RazorCompiledItem(typeof(Views__ViewImports), "mvc.1.0.view", "/Views/_ViewImports.cshtml")]
[assembly: RazorCompiledItem(typeof(Views__ViewStart), "mvc.1.0.view", "/Views/_ViewStart.cshtml")]
[assembly: AssemblyVersion("1.0.0.0")]
[module: RefSafetyRules(11)]
[CompilerGenerated]
internal class Program
{
	private static void <Main>$(string[] args)
	{
		WebApplicationBuilder webApplicationBuilder = WebApplication.CreateBuilder(args);
		webApplicationBuilder.Services.Configure<GameOptions>(webApplicationBuilder.Configuration.GetSection("Game"));
		webApplicationBuilder.Services.Configure<TickOptions>(webApplicationBuilder.Configuration.GetSection("Tick"));
		string flagPath = Environment.GetEnvironmentVariable("FLAG_PATH") ?? "/flag.txt";
		string fallbackFlag = webApplicationBuilder.Configuration["Flag"] ?? "crypto{demo_flag}";
		webApplicationBuilder.Services.AddSingleton((Func<IServiceProvider, IFlagProvider>)((IServiceProvider sp) => new FlagProvider(flagPath, fallbackFlag, sp.GetRequiredService<ILogger<FlagProvider>>())));
		int @int = RandomNumberGenerator.GetInt32(int.MinValue, int.MaxValue);
		webApplicationBuilder.Services.AddSingleton((IRandomSource)new RandomSource(@int));
		webApplicationBuilder.Services.AddSingleton<IPrizeService, PrizeService>();
		webApplicationBuilder.Services.AddSingleton<ITickRngService, TickRngService>();
		webApplicationBuilder.Services.AddHostedService((IServiceProvider sp) => (TickRngService)sp.GetRequiredService<ITickRngService>());
		webApplicationBuilder.Services.AddControllersWithViews();
		WebApplication webApplication = webApplicationBuilder.Build();
		webApplication.UseStaticFiles();
		webApplication.UseRouting();
		webApplication.MapControllerRoute("default", "{controller=Home}/{action=Index}/{id?}");
		webApplication.Run();
	}
}
namespace AspNetCoreGeneratedDocument
{
	[RazorCompiledItemMetadata("Identifier", "/Views/Home/Index.cshtml")]
	[CreateNewOnMetadataUpdate]
	internal sealed class Views_Home_Index : RazorPage<dynamic>
	{
		private TagHelperExecutionContext __tagHelperExecutionContext;

		private TagHelperRunner __tagHelperRunner = new TagHelperRunner();

		private string __tagHelperStringValueBuffer;

		private TagHelperScopeManager __backed__tagHelperScopeManager;

		private OptionTagHelper __Microsoft_AspNetCore_Mvc_TagHelpers_OptionTagHelper;

		private TagHelperScopeManager __tagHelperScopeManager
		{
			get
			{
				if (__backed__tagHelperScopeManager == null)
				{
					__backed__tagHelperScopeManager = new TagHelperScopeManager(base.StartTagHelperWritingScope, base.EndTagHelperWritingScope);
				}
				return __backed__tagHelperScopeManager;
			}
		}

		[RazorInject]
		public IModelExpressionProvider ModelExpressionProvider { get; private set; }

		[RazorInject]
		public IUrlHelper Url { get; private set; }

		[RazorInject]
		public IViewComponentHelper Component { get; private set; }

		[RazorInject]
		public IJsonHelper Json { get; private set; }

		[RazorInject]
		public IHtmlHelper<dynamic> Html { get; private set; }

		public override async Task ExecuteAsync()
		{
			base.ViewData["Title"] = "Ticked RNG";
			WriteLiteral("<section class=\"panel\">\r\n  <div class=\"panel-head\">\r\n    <h2>Current Frame</h2>\r\n    <div class=\"actions\">\r\n      <button id=\"btnRefresh\" class=\"btn\">Refresh</button>\r\n      <label class=\"switch\">\r\n        <input id=\"autoRefresh\" type=\"checkbox\" checked />\r\n        <span>Auto refresh</span>\r\n      </label>\r\n    </div>\r\n  </div>\r\n\r\n  <!-- Slot machine -->\r\n  <div class=\"slots\">\r\n    <div class=\"slot\"><div class=\"reel\" id=\"reel0\"></div></div>\r\n    <div class=\"slot\"><div class=\"reel\" id=\"reel1\"></div></div>\r\n    <div class=\"slot\"><div class=\"reel\" id=\"reel2\"></div></div>\r\n  </div>\r\n\r\n  <div class=\"grid one\">\r\n    <div>\r\n      <h3>Frame</h3>\r\n      <div id=\"frameTable\" class=\"kv\"></div>\r\n    </div>\r\n  </div>\r\n</section>\r\n\r\n<section class=\"panel\">\r\n  <div class=\"panel-head\">\r\n    <h2>Redeem</h2>\r\n  </div>\r\n  <div class=\"row wrap\">\r\n    <input id=\"tickId\" class=\"inp\" placeholder=\"tickId (current or next)\" />\r\n    <input id=\"redeemCode\" class=\"inp\" placeholder=\"code (int)\" />\r\n    <button id=\"btnRedeem\" class=\"btn\">");
			WriteLiteral("Redeem</button>\r\n    <button id=\"btnUseNext\" class=\"btn ghost\" title=\"Prefill next tick\">Use next tick</button>\r\n  </div>\r\n  <div id=\"redeemOutWrap\" class=\"grid two\">\r\n    <div>\r\n      <h3>Redeem Result</h3>\r\n      <pre id=\"redeemOut\" class=\"mono codebox\">—</pre>\r\n    </div>\r\n    <div>\r\n      <h3>flag</h3>\r\n      <div class=\"row\">\r\n        <input id=\"flagHex\" class=\"inp flex\" readonly");
			BeginWriteAttribute("value", " value=\"", 1457, "\"", 1465, 0);
			EndWriteAttribute();
			WriteLiteral(" />\r\n        <button id=\"btnCopyFlag\" class=\"btn ghost\">Copy</button>\r\n      </div>\r\n    </div>\r\n  </div>\r\n</section>\r\n\r\n<section class=\"panel\">\r\n  <div class=\"panel-head\">\r\n    <h2>Recent Frames</h2>\r\n    <div class=\"actions\">\r\n      <select id=\"recentCount\" class=\"inp\">\r\n        ");
			__tagHelperExecutionContext = __tagHelperScopeManager.Begin("option", TagMode.StartTagAndEndTag, "c73cd478b05722a05b6ddfee18af4d9fe9896db2617beb548d68a7a3479be16b4928", async delegate
			{
				WriteLiteral("5");
			});
			__Microsoft_AspNetCore_Mvc_TagHelpers_OptionTagHelper = CreateTagHelper<OptionTagHelper>();
			__tagHelperExecutionContext.Add(__Microsoft_AspNetCore_Mvc_TagHelpers_OptionTagHelper);
			await __tagHelperRunner.RunAsync(__tagHelperExecutionContext);
			if (!__tagHelperExecutionContext.Output.IsContentModified)
			{
				await __tagHelperExecutionContext.SetOutputContentAsync();
			}
			Write(__tagHelperExecutionContext.Output);
			__tagHelperExecutionContext = __tagHelperScopeManager.End();
			__tagHelperExecutionContext = __tagHelperScopeManager.Begin("option", TagMode.StartTagAndEndTag, "c73cd478b05722a05b6ddfee18af4d9fe9896db2617beb548d68a7a3479be16b5870", async delegate
			{
				WriteLiteral("10");
			});
			__Microsoft_AspNetCore_Mvc_TagHelpers_OptionTagHelper = CreateTagHelper<OptionTagHelper>();
			__tagHelperExecutionContext.Add(__Microsoft_AspNetCore_Mvc_TagHelpers_OptionTagHelper);
			await __tagHelperRunner.RunAsync(__tagHelperExecutionContext);
			if (!__tagHelperExecutionContext.Output.IsContentModified)
			{
				await __tagHelperExecutionContext.SetOutputContentAsync();
			}
			Write(__tagHelperExecutionContext.Output);
			__tagHelperExecutionContext = __tagHelperScopeManager.End();
			__tagHelperExecutionContext = __tagHelperScopeManager.Begin("option", TagMode.StartTagAndEndTag, "c73cd478b05722a05b6ddfee18af4d9fe9896db2617beb548d68a7a3479be16b6813", async delegate
			{
				WriteLiteral("15");
			});
			__Microsoft_AspNetCore_Mvc_TagHelpers_OptionTagHelper = CreateTagHelper<OptionTagHelper>();
			__tagHelperExecutionContext.Add(__Microsoft_AspNetCore_Mvc_TagHelpers_OptionTagHelper);
			BeginWriteTagHelperAttribute();
			__tagHelperStringValueBuffer = EndWriteTagHelperAttribute();
			__tagHelperExecutionContext.AddHtmlAttribute("selected", Html.Raw(__tagHelperStringValueBuffer), HtmlAttributeValueStyle.Minimized);
			await __tagHelperRunner.RunAsync(__tagHelperExecutionContext);
			if (!__tagHelperExecutionContext.Output.IsContentModified)
			{
				await __tagHelperExecutionContext.SetOutputContentAsync();
			}
			Write(__tagHelperExecutionContext.Output);
			__tagHelperExecutionContext = __tagHelperScopeManager.End();
			WriteLiteral("\r\n      </select>\r\n      <button id=\"btnRecent\" class=\"btn\">Load</button>\r\n    </div>\r\n  </div>\r\n  <div id=\"recentList\" class=\"cards\"></div>\r\n</section>\r\n");
		}
	}
	[RazorCompiledItemMetadata("Identifier", "/Views/Shared/_Layout.cshtml")]
	[CreateNewOnMetadataUpdate]
	internal sealed class Views_Shared__Layout : RazorPage<dynamic>
	{
		private TagHelperExecutionContext __tagHelperExecutionContext;

		private TagHelperRunner __tagHelperRunner = new TagHelperRunner();

		private string __tagHelperStringValueBuffer;

		private TagHelperScopeManager __backed__tagHelperScopeManager;

		private HeadTagHelper __Microsoft_AspNetCore_Mvc_Razor_TagHelpers_HeadTagHelper;

		private BodyTagHelper __Microsoft_AspNetCore_Mvc_Razor_TagHelpers_BodyTagHelper;

		private TagHelperScopeManager __tagHelperScopeManager
		{
			get
			{
				if (__backed__tagHelperScopeManager == null)
				{
					__backed__tagHelperScopeManager = new TagHelperScopeManager(base.StartTagHelperWritingScope, base.EndTagHelperWritingScope);
				}
				return __backed__tagHelperScopeManager;
			}
		}

		[RazorInject]
		public IModelExpressionProvider ModelExpressionProvider { get; private set; }

		[RazorInject]
		public IUrlHelper Url { get; private set; }

		[RazorInject]
		public IViewComponentHelper Component { get; private set; }

		[RazorInject]
		public IJsonHelper Json { get; private set; }

		[RazorInject]
		public IHtmlHelper<dynamic> Html { get; private set; }

		public override async Task ExecuteAsync()
		{
			WriteLiteral("<!doctype html>\r\n<html>\r\n");
			__tagHelperExecutionContext = __tagHelperScopeManager.Begin("head", TagMode.StartTagAndEndTag, "ec1872481d2c7a45af26deb7ec3a72b934810147db4b8cf9863c23de0c1c0b042963", async delegate
			{
				WriteLiteral("\r\n  <meta charset=\"utf-8\" />\r\n  <title>Lucky Slots</title>\r\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\r\n  <link href=\"/css/site.css\" rel=\"stylesheet\" />\r\n");
			});
			__Microsoft_AspNetCore_Mvc_Razor_TagHelpers_HeadTagHelper = CreateTagHelper<HeadTagHelper>();
			__tagHelperExecutionContext.Add(__Microsoft_AspNetCore_Mvc_Razor_TagHelpers_HeadTagHelper);
			await __tagHelperRunner.RunAsync(__tagHelperExecutionContext);
			if (!__tagHelperExecutionContext.Output.IsContentModified)
			{
				await __tagHelperExecutionContext.SetOutputContentAsync();
			}
			Write(__tagHelperExecutionContext.Output);
			__tagHelperExecutionContext = __tagHelperScopeManager.End();
			WriteLiteral("\r\n");
			__tagHelperExecutionContext = __tagHelperScopeManager.Begin("body", TagMode.StartTagAndEndTag, "ec1872481d2c7a45af26deb7ec3a72b934810147db4b8cf9863c23de0c1c0b044153", async delegate
			{
				WriteLiteral("\r\n  <header class=\"hdr\">\r\n    <div class=\"hdr-inner\">\r\n      <div class=\"brand\">\r\n        <span class=\"logo\">\ud83c\udfb0</span>\r\n        <div>\r\n          <h1>Lucky Slots</h1>\r\n          <p class=\"sub\">A totally secure, definitely-random game.</p>\r\n        </div>\r\n      </div>\r\n      <div class=\"tick\">\r\n        <div class=\"tick-line\">\r\n          <span class=\"dot\"></span>\r\n          <span id=\"tickStatus\">observing…</span>\r\n        </div>\r\n        <div class=\"tick-line small\">\r\n          next tick in <span id=\"tickCountdown\">—</span>\r\n        </div>\r\n      </div>\r\n    </div>\r\n  </header>\r\n\r\n  <main class=\"container\">\r\n    ");
				Write(RenderBody());
				WriteLiteral("\r\n  </main>\r\n\r\n  <footer>\r\n    <small>© 2025</small>\r\n  </footer>\r\n\r\n  <script src=\"/js/app.js\"></script>\r\n");
			});
			__Microsoft_AspNetCore_Mvc_Razor_TagHelpers_BodyTagHelper = CreateTagHelper<BodyTagHelper>();
			__tagHelperExecutionContext.Add(__Microsoft_AspNetCore_Mvc_Razor_TagHelpers_BodyTagHelper);
			await __tagHelperRunner.RunAsync(__tagHelperExecutionContext);
			if (!__tagHelperExecutionContext.Output.IsContentModified)
			{
				await __tagHelperExecutionContext.SetOutputContentAsync();
			}
			Write(__tagHelperExecutionContext.Output);
			__tagHelperExecutionContext = __tagHelperScopeManager.End();
			WriteLiteral("\r\n</html>\r\n");
		}
	}
	[RazorCompiledItemMetadata("Identifier", "/Views/_ViewImports.cshtml")]
	[CreateNewOnMetadataUpdate]
	internal sealed class Views__ViewImports : RazorPage<dynamic>
	{
		[RazorInject]
		public IModelExpressionProvider ModelExpressionProvider { get; private set; }

		[RazorInject]
		public IUrlHelper Url { get; private set; }

		[RazorInject]
		public IViewComponentHelper Component { get; private set; }

		[RazorInject]
		public IJsonHelper Json { get; private set; }

		[RazorInject]
		public IHtmlHelper<dynamic> Html { get; private set; }

		public override async Task ExecuteAsync()
		{
		}
	}
	[RazorCompiledItemMetadata("Identifier", "/Views/_ViewStart.cshtml")]
	[CreateNewOnMetadataUpdate]
	internal sealed class Views__ViewStart : RazorPage<dynamic>
	{
		[RazorInject]
		public IModelExpressionProvider ModelExpressionProvider { get; private set; }

		[RazorInject]
		public IUrlHelper Url { get; private set; }

		[RazorInject]
		public IViewComponentHelper Component { get; private set; }

		[RazorInject]
		public IJsonHelper Json { get; private set; }

		[RazorInject]
		public IHtmlHelper<dynamic> Html { get; private set; }

		public override async Task ExecuteAsync()
		{
			base.Layout = "_Layout";
		}
	}
}
namespace WebGame.Services
{
	public sealed class FlagProvider : IFlagProvider
	{
		private readonly string _path;

		private readonly string _fallback;

		private readonly ILogger<FlagProvider> _log;

		public FlagProvider(string path, string fallback, ILogger<FlagProvider> log)
		{
			_path = path;
			_fallback = fallback;
			_log = log;
		}

		public string GetFlag()
		{
			try
			{
				if (File.Exists(_path))
				{
					return File.ReadAllText(_path).Trim();
				}
			}
			catch (Exception exception)
			{
				_log.LogWarning(exception, "Failed reading flag from {Path}", _path);
			}
			return _fallback;
		}
	}
	public interface IFlagProvider
	{
		string GetFlag();
	}
	public interface IPrizeService
	{
		(string CipherHex, int MaskLen) MaskFlag(string flag);
	}
	public interface IRandomSource
	{
		int Next();

		int Next(int maxValue);

		int Next(int minValue, int maxValue);

		void NextBytes(byte[] buffer);
	}
	public interface ITickRngService
	{
		TickFrame? GetCurrent();

		TickFrame? Get(long tickId);

		IEnumerable<TickFrame> Recent(int count);
	}
	public interface ITokenService
	{
		string IssueToken();
	}
	public sealed class PrizeService(IRandomSource rng) : IPrizeService
	{
		public (string CipherHex, int MaskLen) MaskFlag(string flag)
		{
			byte[] bytes = Encoding.UTF8.GetBytes(flag);
			byte[] array = new byte[bytes.Length];
			rng.NextBytes(array);
			byte[] array2 = new byte[bytes.Length];
			for (int i = 0; i < bytes.Length; i++)
			{
				array2[i] = (byte)(bytes[i] ^ array[i]);
			}
			return (CipherHex: Convert.ToHexString(array2).ToLowerInvariant(), MaskLen: array.Length);
		}
	}
	public sealed class RandomSource : IRandomSource
	{
		private readonly Random _rng;

		private readonly object _lock = new object();

		public int SeedSeconds { get; }

		public RandomSource(int seedSeconds)
		{
			SeedSeconds = seedSeconds;
			_rng = new Random(seedSeconds);
			byte[] buffer = new byte[64];
			_rng.NextBytes(buffer);
			_rng.Next(0, 1000000);
			_rng.Next();
		}

		public int Next()
		{
			lock (_lock)
			{
				return _rng.Next();
			}
		}

		public int Next(int maxValue)
		{
			lock (_lock)
			{
				return _rng.Next(maxValue);
			}
		}

		public int Next(int minValue, int maxValue)
		{
			lock (_lock)
			{
				return _rng.Next(minValue, maxValue);
			}
		}

		public void NextBytes(byte[] buffer)
		{
			lock (_lock)
			{
				_rng.NextBytes(buffer);
			}
		}
	}
	public sealed class TickRngService : BackgroundService, ITickRngService
	{
		private readonly IRandomSource _rng;

		private readonly IPrizeService _prize;

		private readonly TickOptions _opts;

		private readonly GameOptions _game;

		private readonly ConcurrentDictionary<long, TickFrame> _frames = new ConcurrentDictionary<long, TickFrame>();

		private long _currentTickId;

		public TickRngService(IRandomSource rng, IPrizeService prize, IOptions<TickOptions> tickOptions, IOptions<GameOptions> gameOptions)
		{
			_rng = rng;
			_prize = prize;
			_opts = tickOptions.Value;
			_game = gameOptions.Value;
		}

		protected override async Task ExecuteAsync(CancellationToken stoppingToken)
		{
			await Task.Delay(TimeSpan.FromMilliseconds(1000 - DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() % 1000), stoppingToken);
			TimeSpan period = TimeSpan.FromSeconds(Math.Max(1, _opts.PeriodSeconds));
			PeriodicTimer timer = new PeriodicTimer(period);
			ProduceNextFrame();
			while (await timer.WaitForNextTickAsync(stoppingToken))
			{
				ProduceNextFrame();
				TrimHistory();
			}
		}

		private void ProduceNextFrame()
		{
			long num = Interlocked.Increment(ref _currentTickId);
			long unixSeconds = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
			int num2 = _rng.Next(10);
			int num3 = _rng.Next(10);
			int num4 = _rng.Next(10);
			int jackpotPreview = _rng.Next(_game.JackpotMax);
			int[] array = new int[_opts.SampleIntCount];
			for (int i = 0; i < array.Length; i++)
			{
				array[i] = _rng.Next(int.MaxValue);
			}
			byte[] array2 = new byte[_opts.SampleByteLen];
			_rng.NextBytes(array2);
			int redeemCode = _rng.Next(_game.RedeemMax);
			TickFrame tickFrame = new TickFrame();
			tickFrame.TickId = num;
			tickFrame.UnixSeconds = unixSeconds;
			tickFrame.Reels = new int[3] { num2, num3, num4 };
			tickFrame.JackpotPreview = jackpotPreview;
			tickFrame.SampleInts = array;
			tickFrame.SampleBytesHex = Convert.ToHexString(array2).ToLowerInvariant();
			tickFrame.RedeemCode = redeemCode;
			TickFrame value = tickFrame;
			_frames[num] = value;
		}

		private void TrimHistory()
		{
			int num = Math.Max(10, _opts.HistorySize);
			long num2 = _currentTickId - num;
			foreach (long key in _frames.Keys)
			{
				if (key < num2)
				{
					_frames.TryRemove(key, out TickFrame _);
				}
			}
		}

		public TickFrame? GetCurrent()
		{
			return Get(_currentTickId);
		}

		public TickFrame? Get(long tickId)
		{
			if (!_frames.TryGetValue(tickId, out TickFrame value))
			{
				return null;
			}
			return value;
		}

		public IEnumerable<TickFrame> Recent(int count)
		{
			long max = _currentTickId;
			long num = Math.Max(1L, max - Math.Max(1, count) + 1);
			for (long i = num; i <= max; i++)
			{
				if (_frames.TryGetValue(i, out TickFrame value))
				{
					yield return value;
				}
			}
		}
	}
	public sealed class TokenService(IRandomSource rng) : ITokenService
	{
		public string IssueToken()
		{
			byte[] array = new byte[16];
			rng.NextBytes(array);
			return Convert.ToHexString(array).ToLowerInvariant();
		}
	}
}
namespace WebGame.Models
{
	public sealed class GameOptions
	{
		public int JackpotMax { get; set; } = 1000000;

		public int RedeemMax { get; set; } = 10000000;
	}
	public sealed class RedeemRequest
	{
		[JsonPropertyName("code")]
		public int Code { get; set; }
	}
	public sealed record SpinResult(int[] Reels, int JackpotPreview, string SessionToken);
	public sealed class TickFrame
	{
		public long TickId { get; init; }

		public long UnixSeconds { get; init; }

		public int[] Reels { get; init; } = Array.Empty<int>();

		public int JackpotPreview { get; init; }

		public int[] SampleInts { get; init; } = Array.Empty<int>();

		public string SampleBytesHex { get; init; } = "";

		public int RedeemCode { get; init; }
	}
	public sealed class TickOptions
	{
		public int PeriodSeconds { get; set; } = 2;

		public int HistorySize { get; set; } = 30;

		public int SampleIntCount { get; set; } = 16;

		public int SampleByteLen { get; set; } = 4;
	}
}
namespace WebGame.Controllers
{
	[Route("api")]
	[ApiController]
	public sealed class ApiController(ITickRngService ticks, IFlagProvider flag) : ControllerBase()
	{
		public sealed class RedeemReq
		{
			public long TickId { get; set; }

			public int Code { get; set; }
		}

		[HttpGet("frame")]
		public ActionResult<object> Current()
		{
			TickFrame current = ticks.GetCurrent();
			if (current == null)
			{
				return Problem("No frame yet.");
			}
			return Ok(Public(current));
		}

		[HttpGet("frame/{tickId:long}")]
		public ActionResult<object> Get(long tickId)
		{
			TickFrame tickFrame = ticks.Get(tickId);
			if (tickFrame == null)
			{
				return NotFound(new
				{
					message = "Unknown tickId"
				});
			}
			return Ok(Public(tickFrame));
		}

		[HttpGet("recent/{n:int}")]
		public ActionResult<IEnumerable<object>> Recent(int n = 5)
		{
			IEnumerable<object> value = ticks.Recent(Math.Clamp(n, 1, 30)).Select(Public);
			return Ok(value);
		}

		[HttpPost("redeem")]
		public IActionResult Redeem([FromBody] RedeemReq req)
		{
			TickFrame tickFrame = ticks.Get(req.TickId);
			if (tickFrame == null)
			{
				return NotFound(new
				{
					success = false,
					message = "Unknown tickId"
				});
			}
			if (req.Code != tickFrame.RedeemCode)
			{
				return StatusCode(403, new
				{
					success = false,
					message = "Wrong code."
				});
			}
			string flag = flag.GetFlag();
			return Ok(new
			{
				success = true,
				message = "Jackpot!",
				tickId = tickFrame.TickId,
				flag = flag
			});
		}

		private static object Public(TickFrame f)
		{
			return new
			{
				tickId = f.TickId,
				unixSeconds = f.UnixSeconds,
				reels = f.Reels,
				jackpotPreview = f.JackpotPreview,
				sampleInts = f.SampleInts,
				sampleBytesHex = f.SampleBytesHex
			};
		}
	}
	public sealed class HomeController : Controller
	{
		public IActionResult Index()
		{
			return View();
		}
	}
}
