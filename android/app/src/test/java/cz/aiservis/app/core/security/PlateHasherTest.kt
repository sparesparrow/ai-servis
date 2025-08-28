package cz.aiservis.app.core.security

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test

class PlateHasherTest {
	@Test
	fun normalize_replacesAmbiguousChars() {
		val n = PlateHasher.normalize(" ab0 b o ")
		assertEquals("AB08 0".replace(" ", ""), n)
	}

	@Test
	fun hmac_sameInputSameSecret_sameHash() {
		val secret = ByteArray(16) { 1 }
		val a = PlateHasher.hmacSha256("2ab 1234", secret)
		val b = PlateHasher.hmacSha256("2ab 1234", secret)
		assertEquals(a, b)
	}

	@Test
	fun hmac_differentSecret_differentHash() {
		val a = PlateHasher.hmacSha256("2ab1234", ByteArray(16) { 1 })
		val b = PlateHasher.hmacSha256("2ab1234", ByteArray(16) { 2 })
		assertNotEquals(a, b)
	}
}
