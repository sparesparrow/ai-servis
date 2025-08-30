package cz.aiservis.app

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.BottomAppBar
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Snackbar
import androidx.compose.material3.SnackbarDefaults
import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import cz.aiservis.app.core.background.DrivingService
import cz.aiservis.app.core.background.SamplingMode
import cz.aiservis.app.data.db.AlertEntity
import cz.aiservis.app.data.db.AnprEventEntity
import cz.aiservis.app.data.db.ClipEntity
import cz.aiservis.app.data.db.TelemetryEntity
import cz.aiservis.app.features.alerts.AlertsViewModel
import cz.aiservis.app.features.anpr.AnprViewModel
import cz.aiservis.app.features.clips.ClipsViewModel
import cz.aiservis.app.features.dashboard.DashboardViewModel
import cz.aiservis.app.features.dashboard.PolicyViewModel
import cz.aiservis.app.features.settings.SettingsViewModel
import cz.aiservis.app.ui.components.DashboardGauges

class MainActivity : ComponentActivity() {
	override fun onCreate(savedInstanceState: Bundle?) {
		super.onCreate(savedInstanceState)
		setContent { AppRoot() }
	}

	private fun startDrivingService() {
		val intent = Intent(this, DrivingService::class.java).apply { action = DrivingService.ACTION_START }
		startForegroundService(intent)
	}

	private fun stopDrivingService() {
		val intent = Intent(this, DrivingService::class.java).apply { action = DrivingService.ACTION_STOP }
		startService(intent)
	}

	@OptIn(ExperimentalMaterial3Api::class)
	@Composable
	private fun AppRoot() {
		var selected by remember { mutableStateOf(0) }
		val snackbarHostState: SnackbarHostState = remember { SnackbarHostState() }
		Scaffold(
			snackbarHost = { SnackbarHost(snackbarHostState) },
			bottomBar = {
				NavigationBar {
					NavigationBarItem(
						selected = selected == 0,
						onClick = { selected = 0 },
						icon = { Icon(Icons.Default.Dashboard, contentDescription = null) },
						label = { Text("Dashboard") }
					)
					NavigationBarItem(
						selected = selected == 1,
						onClick = { selected = 1 },
						icon = { Icon(Icons.Default.Warning, contentDescription = null) },
						label = { Text("Alerts") }
					)
					NavigationBarItem(
						selected = selected == 2,
						onClick = { selected = 2 },
						icon = { Icon(Icons.Default.CameraAlt, contentDescription = null) },
						label = { Text("ANPR") }
					)
					NavigationBarItem(
						selected = selected == 3,
						onClick = { selected = 3 },
						icon = { Icon(Icons.Default.VideoLibrary, contentDescription = null) },
						label = { Text("Clips") }
					)
					NavigationBarItem(
						selected = selected == 4,
						onClick = { selected = 4 },
						icon = { Icon(Icons.Default.Settings, contentDescription = null) },
						label = { Text("Settings") }
					)
				}
			}
		) { padding ->
			when (selected) {
				0 -> DashboardScreen(Modifier.padding(padding))
				1 -> AlertsScreen(Modifier.padding(padding))
				2 -> AnprScreen(Modifier.padding(padding))
				3 -> ClipsScreen(Modifier.padding(padding))
				else -> SettingsScreen(Modifier.padding(padding))
			}
		}
	}

	@Composable
	private fun DashboardScreen(modifier: Modifier = Modifier) {
		val vm: DashboardViewModel = hiltViewModel()
		val policyVm: PolicyViewModel = hiltViewModel()
		val latest = vm.latest.value
		val policy = policyVm.state.value
		Column(modifier = modifier.fillMaxSize().padding(16.dp)) {
			Text("Dashboard")
			PolicyAdvisory(policy.advisoryMessage, policy.samplingMode.name, policy.batteryPercent)
			Spacer(Modifier.height(8.dp))
			DashboardGauges(latest)
			Spacer(Modifier.height(16.dp))
			Button(onClick = { startDrivingService() }) { Text("Start Driving Service") }
			Spacer(Modifier.height(8.dp))
			Button(onClick = { stopDrivingService() }) { Text("Stop Driving Service") }
		}
	}

	@Composable
	private fun TelemetrySummary(latest: TelemetryEntity?) {
		if (latest == null) {
			Text("No telemetry yet")
		} else {
			Text("Fuel: ${latest.fuelLevel}%  RPM: ${latest.engineRpm}  Speed: ${latest.vehicleSpeed} km/h  Coolant: ${latest.coolantTemp}°C")
		}
	}

	@Composable
	private fun AlertsScreen(modifier: Modifier = Modifier) {
		val vm: AlertsViewModel = hiltViewModel()
		LazyColumn(modifier = modifier.fillMaxSize().padding(16.dp)) {
			items(vm.recent.value) { alert: AlertEntity ->
				Text("[${alert.severity}] ${alert.message}")
			}
		}
	}

	@Composable
	private fun AnprScreen(modifier: Modifier = Modifier) {
		val vm: AnprViewModel = hiltViewModel()
		LazyColumn(modifier = modifier.fillMaxSize().padding(16.dp)) {
			items(vm.recent.value) { ev: AnprEventEntity ->
				Text("ANPR: ${ev.plateHash.take(8)}…  conf=${ev.confidence}")
			}
		}
	}

	@Composable
	private fun ClipsScreen(modifier: Modifier = Modifier) {
		val vm: ClipsViewModel = hiltViewModel()
		val clips by vm.clips.collectAsState(initial = emptyList())
		LazyColumn(modifier = modifier.fillMaxSize().padding(16.dp)) {
			items(clips) { clip: ClipEntity ->
				Text("Clip: ${clip.reason}  ${clip.filePath}  offloaded=${clip.offloaded}")
			}
		}
	}

	@Composable
	private fun SettingsScreen(modifier: Modifier = Modifier) {
		val vm: SettingsViewModel = hiltViewModel()
		val currentVin = vm.vin.value
		var vinText by remember(currentVin) { mutableStateOf(currentVin) }
		val incognito = vm.incognito.value
		val retention = vm.retentionDays.value.toFloat()
		val metrics = vm.metricsOptIn.value
		val region = vm.anprRegion.value
		var lastExportPath by remember { mutableStateOf("") }

		Column(modifier = modifier.padding(16.dp)) {
			Text(text = "Settings")
			Spacer(modifier = Modifier.height(12.dp))
			OutlinedTextField(value = vinText, onValueChange = { vinText = it }, label = { Text("VIN") })
			Spacer(modifier = Modifier.height(8.dp))
			Button(onClick = { vm.setVin(vinText) }) { Text("Save VIN") }
			Spacer(modifier = Modifier.height(16.dp))
			Text("Incognito")
			Switch(checked = incognito, onCheckedChange = { vm.setIncognito(it) })
			Spacer(modifier = Modifier.height(8.dp))
			Text("Retention: ${retention.toInt()} days")
			Slider(value = retention, onValueChange = { vm.setRetentionDays(it.toInt()) }, valueRange = 1f..30f)
			Spacer(Modifier.height(16.dp))
			Text("Metrics opt-in (health pings)")
			Switch(checked = metrics, onCheckedChange = { vm.setMetricsOptIn(it) })
			Spacer(Modifier.height(16.dp))
			Text("ANPR Region: ${region}")
			RowToggle(options = listOf("CZ", "EU"), selected = region, onSelected = { vm.setAnprRegion(it) })
			Spacer(Modifier.height(16.dp))
			Button(onClick = {
				vm.exportLogs { file -> lastExportPath = file.absolutePath }
			}) { Text("Export Logs") }
			if (lastExportPath.isNotEmpty()) {
				Spacer(Modifier.height(8.dp))
				Text("Exported: ${lastExportPath}")
			}
		}
	}
}
@Composable
private fun PolicyAdvisory(message: String?, mode: String, battery: Int) {
	if (!message.isNullOrBlank()) {
		Snackbar(
			shape = SnackbarDefaults.shape,
			action = { Text("Mode: ${mode}") }
		) {
			Text("${message}  •  Battery ${battery}%")
		}
	}
}


@Composable
private fun RowToggle(options: List<String>, selected: String, onSelected: (String) -> Unit) {
	Row {
		options.forEach { opt ->
			Button(onClick = { onSelected(opt) }, enabled = opt != selected) { Text(opt) }
			Spacer(Modifier.height(0.dp))
		}
	}
}
