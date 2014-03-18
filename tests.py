import unittest
import parsefacilities
from mock import Mock, call, patch
import datetime 
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
			INSERT INTO facilities (id, name, lastupdate, creation, address)
				VALUES ( ?, ?, ?, ?, ? );''', 
				('someID', 'Test facility', default_date, default_date, '123 King St E'))]

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


if __name__ == '__main__':
    unittest.main()