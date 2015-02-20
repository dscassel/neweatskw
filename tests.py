import unittest
import parsefacilities
import dbhandler
import tweeteats
from mock import Mock, call, patch
import datetime 


class ParseFacilitiesTests( unittest.TestCase ):
	def test_restaurantRecognizerTrue(self):
		self.assertTrue(parsefacilities.restaurantRecognizer( 'Food, General - Restaurant' ))

		self.assertTrue(parsefacilities.restaurantRecognizer( 'Food, General - Food Take Out' ))

		self.assertTrue(parsefacilities.restaurantRecognizer( 'Food, General - Bakery - Production' ))

	def test_restaurantRecognizerFalse(self):
		self.assertFalse(parsefacilities.restaurantRecognizer( 'Food, General - Supermarket' ))

	def test_cityRecognizerTrue(self):
		self.assertTrue(parsefacilities.cityRecognizer( 'WATERLOO' ))

		self.assertTrue(parsefacilities.cityRecognizer( 'KITCHENER' ))

	def test_cityRecognizerFalse(self):
		self.assertFalse(parsefacilities.cityRecognizer( 'AUCKLAND' ))

	def test_getFacilities(self):
		test_csv_entries = open('testdata/DBHelper_TestData.csv')
		entries = [i for i in parsefacilities.getFacilities(test_csv_entries)]

		flying_squirrel_cafe = entries[0]
		alligator_pies = entries[1]

		self.assertEqual( 'Food, General - Restaurant', flying_squirrel_cafe['Type'])
		self.assertEqual('WATERLOO', flying_squirrel_cafe['City'])
		self.assertEqual('321 QUEEN ST N', flying_squirrel_cafe['Address'])
		self.assertEqual('FLYING SQUIRREL CAFE', flying_squirrel_cafe['Name'])

		self.assertEqual( 'Food, General - Bakery - Production', alligator_pies['Type'])
		self.assertEqual('KITCHENER', alligator_pies['City'])
		self.assertEqual('123 KING ST', alligator_pies['Address'])
		self.assertEqual('ALLIGATOR PIES', alligator_pies['Name'])

class DBTests( unittest.TestCase ):
	def setUp(self):
		self.details = { 
			'ID': 'someID', 
			'Name': 'Test facility',
			'Type': 'Food, General: Restaurant',
			'City': 'WATERLOO',
			'Address': "123 King St E" }

		self.cursor = Mock()
		self.cursor.execute = Mock()
		self.cursor.fetchone = Mock()


	@patch('parsefacilities.datetime.datetime')
	def test_newrecord(self, MockDate):
		default_date = datetime.datetime( 2001, 1, 1, 1, 1, 1 )
		MockDate.now.return_value = default_date

		self.cursor.fetchone.return_value = None
		parsefacilities.addToDB( self.cursor, self.details)
		self.cursor.fetchone.assert_called_once_with()
		expected_calls = [
			call("SELECT * FROM facilities WHERE id=?;", ('someID',)),
			call('''
			INSERT INTO facilities (id, name, lastupdate, creation, address, city)
				VALUES ( ?, ?, ?, ?, ?, ? );''', 
					('someID', 'Test facility', default_date, default_date, '123 King St E', 'WATERLOO'))]
		self.cursor.execute.assert_has_calls( expected_calls )
		
	@patch('parsefacilities.datetime.datetime')
	def test_existingrecord( self, MockDate ):
		default_date = datetime.datetime( 2001, 1, 1, 1, 1, 1 )
		MockDate.now.return_value = default_date
		
		self.cursor.fetchone.return_value = ('someID',)

		parsefacilities.addToDB( self.cursor, self.details )
		self.cursor.fetchone.assert_called_once_with()

		expected_calls = [
			call("SELECT * FROM facilities WHERE id=?;", ('someID',)),
			call("UPDATE facilities SET lastupdate = ? WHERE id = ?;", (default_date, 'someID' ) )
		]

		self.cursor.execute.assert_has_calls( expected_calls )

	def test_outofcity( self ):
		self.details['City'] = 'Auckland'
		parsefacilities.addToDB( self.cursor, self.details )

		self.assertEqual( 0, self.cursor.fetchone.call_count )
		self.assertEqual( 0, self.cursor.execute.call_count )

	def test_notrestaurant( self ):
		self.details['Type'] = 'Dentist'
		parsefacilities.addToDB( self.cursor, self.details )

		self.assertEqual( 0, self.cursor.fetchone.call_count )
		self.assertEqual( 0, self.cursor.execute.call_count )

class tweetTests(unittest.TestCase):

	def test_tweetmessage( self ):
		newRestaurant = dbhandler.Facility('blah', 'NEW RESTAURANT', 'blah', 'blah', '123 King St N', 'WATERLOO')
		message = tweeteats.getMessage(newRestaurant)

		self.assertEqual( 'NEW RESTAURANT: 123 King St N, WATERLOO', message )

	def test_tweetNKFM( self ):
		newRestaurant = dbhandler.Facility('blah', 'NKFM-NEW RESTAURANT', 'blah', 'blah', '300 KING ST E', 'KITCHENER')
		message = tweeteats.getMessage(newRestaurant)

		self.assertEqual( "NEW RESTAURANT (Kitchener Farmer's Market): 300 KING ST E, KITCHENER", message )


if __name__ == '__main__':
    unittest.main()
